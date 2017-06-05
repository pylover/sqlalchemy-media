from typing import Tuple, AnyStr
import unittest
import threading
import functools
import contextlib
import json
import shutil
import io
import base64
from os import makedirs, urandom
from os.path import join, dirname, abspath, exists, split
from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer

import requests
from sqlalchemy import Unicode, TypeDecorator, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import paramiko
import mockssh
from mockssh.server import SERVER_KEY_PATH

from sqlalchemy_media import StoreManager, FileSystemStore
from sqlalchemy_media.typing_ import FileLike
from sqlalchemy_media.helpers import copy_stream
from sqlalchemy_media.mimetypes_ import guess_type
from sqlalchemy_media.ssh import SSHClient

Address = Tuple[str, int]


@contextlib.contextmanager
def simple_http_server(handler_class, server_class=HTTPServer, app=None, bind: Address = ('', 0)):
    server = server_class(bind, handler_class)
    if app:
        server.set_app(app)
    thread = threading.Thread(target=server.serve_forever, name='sa-media test server.', daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join()


def mockup_http_static_server(content: bytes = b'Simple file content.', content_type: str = None, **kwargs):
    class StaticMockupHandler(BaseHTTPRequestHandler):  # pragma: no cover
        def serve_text(self):
            self.send_header('Content-Type', "text/plain")
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Last-Modified', self.date_time_string())
            self.end_headers()
            self.wfile.write(content)

        def serve_static_file(self, filename: AnyStr):
            self.send_header('Content-Type', guess_type(filename))
            with open(filename, 'rb') as f:
                self.serve_stream(f)

        def serve_stream(self, stream: FileLike):
            buffer = io.BytesIO()
            self.send_header('Content-Length', str(copy_stream(stream, buffer)))
            self.end_headers()
            buffer.seek(0)
            try:
                copy_stream(buffer, self.wfile)
            except ConnectionResetError:
                pass

        # noinspection PyPep8Naming
        def do_GET(self):
            self.send_response(HTTPStatus.OK)
            if isinstance(content, bytes):
                self.serve_text()
            elif isinstance(content, str):
                self.serve_static_file(content)
            else:
                self.send_header('Content-Type', content_type)
                # noinspection PyTypeChecker
                self.serve_stream(content)

    return simple_http_server(StaticMockupHandler, **kwargs)


@contextlib.contextmanager
def mockup_s3_server(bucket, **kwargs):
    from moto.server import DomainDispatcherApplication, create_backend_app
    mock_app = DomainDispatcherApplication(create_backend_app, 's3')
    mock_app.debug = False
    with simple_http_server(WSGIRequestHandler,  server_class=WSGIServer, app=mock_app, **kwargs) as server:
        url = 'http://localhost:%s' % server.server_address[1]
        # Create the bucket
        bucket_uri = '%s/%s' % (url, bucket)
        res = requests.put(bucket_uri)
        assert res.status_code == 200
        yield server, bucket_uri


# noinspection PyAbstractClass
class Json(TypeDecorator):  # pragma: no cover
    impl = Unicode

    def process_bind_param(self, value, engine):
        return json.dumps(value)

    def process_result_value(self, value, engine):
        if value is None:
            return None

        return json.loads(value)


class SqlAlchemyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_uri = 'sqlite:///:memory:'

    def setUp(self):
        self.Base = declarative_base()
        self.engine = create_engine(self.db_uri, echo=False)

    def create_all_and_get_session(self):
        self.Base.metadata.create_all(self.engine, checkfirst=True)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=True,
            twophase=False
        )
        return self.session_factory()


class TempStoreTestCase(SqlAlchemyTestCase):
    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')

        # Pointing to some handy files.
        cls.dog_jpeg = join(cls.stuff_path, 'dog.jpg')
        cls.cat_jpeg = join(cls.stuff_path, 'cat.jpg')
        cls.dog_png = join(cls.stuff_path, 'dog.png')
        cls.cat_png = join(cls.stuff_path, 'cat.png')

        super().setUpClass()

    def setUp(self):
        self.temp_path = join(self.this_dir, 'temp', self.__class__.__name__, self._testMethodName)
        self.sys_temp_path = join('/tmp/sa-media-tests', self.__class__.__name__, self._testMethodName)
        self.base_url = 'http://static1.example.orm'

        # Remove previous files, if any! to make a clean temp directory:
        if exists(self.temp_path):  # pragma: no cover
            shutil.rmtree(self.temp_path)

        makedirs(self.temp_path)

        StoreManager.register('fs', functools.partial(FileSystemStore, self.temp_path, self.base_url), default=True)
        StoreManager.register(
            'temp_fs',
            functools.partial(FileSystemStore, self.sys_temp_path, self.base_url)
        )
        super().setUp()


def encode_multipart_data(fields: dict = None, files: dict = None):  # pragma: no cover
    boundary = ''.join(['-----', base64.urlsafe_b64encode(urandom(27)).decode()])
    crlf = b'\r\n'
    lines = []

    if fields:
        for key, value in fields.items():
            lines.append('--' + boundary)
            lines.append('Content-Disposition: form-data; name="%s"' % key)
            lines.append('')
            lines.append(value)

    if files:
        for key, file_path in files.items():
            filename = split(file_path)[1]
            lines.append('--' + boundary)
            lines.append(
                'Content-Disposition: form-data; name="%s"; filename="%s"' %
                (key, filename))
            lines.append(
                'Content-Type: %s' %
                (guess_type(filename) or 'application/octet-stream'))
            lines.append('')
            lines.append(open(file_path, 'rb').read())

    lines.append('--' + boundary + '--')
    lines.append('')

    body = io.BytesIO()
    length = 0
    for l in lines:
        # noinspection PyTypeChecker
        line = (l if isinstance(l, bytes) else l.encode()) + crlf
        length += len(line)
        body.write(line)
    body.seek(0)
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body, length


class MockupSSHServer(mockssh.Server):
    def client(self, uid):
        private_key_path, _ = self._users[uid]
        client = SSHClient()
        host_keys = client.get_host_keys()
        key = paramiko.RSAKey.from_private_key_file(SERVER_KEY_PATH)
        host_keys.add(self.host, "ssh-rsa", key)
        host_keys.add("[%s]:%d" % (self.host, self.port), "ssh-rsa", key)
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(
            hostname=self.host,
            port=self.port,
            username=uid,
            key_filename=private_key_path,
            allow_agent=False,
            look_for_keys=False
        )
        return client


class MockupSSHTestCase(SqlAlchemyTestCase):
    def setUp(self):
        self.here = abspath(dirname(__file__))
        self.relative_temp_path = join('temp', self.__class__.__name__, self._testMethodName)
        self.temp_path = join(self.here, self.relative_temp_path)
        # Remove previous files, if any! to make a clean temp directory:
        if exists(self.temp_path):  # pragma: no cover
            shutil.rmtree(self.temp_path)

        makedirs(self.temp_path)

        self.users = {
            'test': join(self.here, 'stuff', 'test-id_rsa')
        }
        self.server = MockupSSHServer(self.users)
        self.server.__enter__()

    def create_ssh_client(self):
        client = self.server.client('test')
        return client

    def tearDown(self):
        self.server.__exit__()
