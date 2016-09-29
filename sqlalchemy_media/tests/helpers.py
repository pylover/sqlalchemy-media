from typing import Tuple
import unittest
import threading
import time
import functools
import contextlib
import json
import shutil
from os import makedirs
from os.path import join, dirname, abspath, exists
from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus

from sqlalchemy import Unicode, TypeDecorator, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_media import StoreManager, FileSystemStore


Address = Tuple[str, int]


@contextlib.contextmanager
def simple_http_server(content: bytes= b'Simple file content.', bind: Address=('', 0)):

    class SimpleHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', "text/plain")
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Last-Modified', self.date_time_string())
            self.end_headers()
            self.wfile.write(content)

    http_server = HTTPServer(bind, SimpleHandler)
    thread = threading.Thread(target=http_server.serve_forever, name='sa-media test server.', daemon=True)
    thread.start()
    yield http_server
    http_server.shutdown()
    thread.join()


# noinspection PyAbstractClass
class Json(TypeDecorator):
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
        super().setUpClass()

    def setUp(self):
        self.temp_path = join(self.this_dir, 'temp', self.__class__.__name__, self._testMethodName)
        self.base_url = 'http://static1.example.orm'

        # Remove previous files, if any! to make a clean temp directory:
        if exists(self.temp_path):
            shutil.rmtree(self.temp_path)

        makedirs(self.temp_path)

        StoreManager.register('fs', functools.partial(FileSystemStore, self.temp_path, self.base_url), default=True)
        super().setUp()


if __name__ == '__main__':
    with simple_http_server(bind=('', 8080), content=b'simple text') as httpd:
        target_url = 'http://%s:%s' % httpd.server_address
        print(target_url)
        time.sleep(1)
