import errno
import io
import os
import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
from multiprocessing import Process
from os.path import join, dirname, abspath, getsize

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import File
from sqlalchemy_media.exceptions import OS2Error
from sqlalchemy_media.helpers import copy_stream
from sqlalchemy_media.stores import OS2Store
from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.tests.helpers import Json, SqlAlchemyTestCase

REAL_TEST = False

TEST_BUCKET = 'sa-media-test'
TEST_ACCESS_KEY = 'sa-media-ak'
TEST_SECRET_KEY = 'sa-media-sk'
TEST_REGION = 'sa-media'
TEST_BIND = ('127.0.0.1', 12208)


def _get_os2_store(bucket=TEST_BUCKET, **kwargs):
    base_headers = {}
    if not REAL_TEST:
        OS2Store.BASE_URL_FORMAT = 'http://{0}:{1}'.format(*TEST_BIND)
        base_headers = {'HOST': '{0}.oss-{1}.{2}:{3}'.format(bucket, TEST_REGION, *TEST_BIND)}
    return OS2Store(bucket, TEST_ACCESS_KEY, TEST_SECRET_KEY, TEST_REGION,
                    base_headers=base_headers, **kwargs)


def _mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # pragma: no cover
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def _create_test_bucket(temp_path, bucket=TEST_BUCKET):
    _mkdirs(os.path.join(temp_path, bucket))


def os2_server(temp_path, bind=TEST_BIND):

    class SimpleHandler(BaseHTTPRequestHandler):  # pragma: no cover

        def _validate_host(self):
            host = self.headers['HOST']
            try:
                bucket, region, *_ = host.split('.')
            except ValueError:
                return self.send_error(400, 'BadRequest')
            if region != 'oss-sa-media':
                return self.send_error(400, 'BadRegionError')
            if not os.path.exists(os.path.join(temp_path, bucket)):
                return self.send_error(400, 'BadBucketError')
            return bucket, region

        # noinspection PyPep8Naming
        def do_GET(self):
            try:
                bucket, _ = self._validate_host()
            except TypeError:
                return
            if self.path == '/':
                return self.send_error('400', 'BadObjectError')

            filename = os.path.join(temp_path, bucket, self.path[1:])
            if not os.path.exists(filename):
                return self.send_error(404, 'NotFound')

            self.send_response(HTTPStatus.OK)
            with open(filename, 'rb') as f:
                data = f.read()
                self.send_header('Content-Length', len(data))
                self.end_headers()
                f.seek(0)
                try:
                    copy_stream(f, self.wfile)
                except ConnectionResetError:
                    pass

        # noinspection PyPep8Naming
        def do_PUT(self):
            try:
                bucket, _ = self._validate_host()
            except TypeError:
                return
            if self.path == '/':
                return self.send_error('400', 'BadObjectError')
            filename = self.path[1:]
            content_len = int(self.headers.get('content-length', 0))
            content = self.rfile.read(content_len)
            filename = os.path.join(temp_path, bucket, filename)
            path = '/'.join(filename.split('/')[:-1])
            _mkdirs(path)
            with open(filename, 'wb') as f:
                f.write(content)
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', "text/plain")
            self.end_headers()

        # noinspection PyPep8Naming
        def do_DELETE(self):
            try:
                bucket, _ = self._validate_host()
            except TypeError:
                return
            if self.path == '/':
                return self.send_error('400', 'BadObjectError')

            filename = os.path.join(temp_path, bucket, self.path[1:])
            if not os.path.exists(filename):
                return self.send_error(404, 'NotFound')

            os.remove(filename)
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', "text/plain")
            self.end_headers()

    return HTTPServer(bind, SimpleHandler)


class OS2StoreTestCase(SqlAlchemyTestCase):

    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')

        # Pointing to some handy files.
        cls.dog_jpeg = join(cls.stuff_path, 'dog.jpg')

        # Mock Server
        if not REAL_TEST:
            temp_path = join(cls.this_dir, 'temp', cls.__name__)
            _create_test_bucket(temp_path)
            server = os2_server(temp_path)
            cls.server_p = Process(target=server.serve_forever)
            cls.server_p.daemon = True
            cls.server_p.start()

        super(OS2StoreTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if not REAL_TEST and hasattr(cls, 'server_p'):
            cls.server_p.terminate()

    def setUp(self):
        super(OS2StoreTestCase, self).setUp()
        self.base_url = 'http://static1.example.orm'
        self.this_dir = abspath(dirname(__file__))
        self.stuff_path = join(self.this_dir, 'stuff')
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def test_put_from_stream(self):
        store = _get_os2_store()
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)
        length = store.put(target_filename, stream)
        self.assertEqual(length, len(content))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

    def test_put_error(self):
        store = _get_os2_store(bucket='{0}-2'.format(TEST_BUCKET))
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)

        with self.assertRaises(OS2Error):
            store.put(target_filename, stream)

    def test_delete(self):
        store = _get_os2_store()
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        store.delete(target_filename)

        with self.assertRaises(OS2Error):
            store.open(target_filename)

    def test_delete_error(self):
        store = _get_os2_store()
        wrong_store = _get_os2_store(bucket='{0}-2'.format(TEST_BUCKET))
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        with self.assertRaises(OS2Error):
            wrong_store.delete(target_filename)

    def test_open(self):
        store = _get_os2_store()
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        # Reading
        with store.open(target_filename, mode='rb') as stored_file, \
                open(self.sample_text_file1, mode='rb') as original_file:
            self.assertEqual(stored_file.read(), original_file.read())

    def test_locate(self):
        store = _get_os2_store()
        StoreManager.register('s3', lambda: store, default=True)

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            file = Column(File.as_mutable(Json))

        session = self.create_all_and_get_session()

        person1 = Person()
        self.assertIsNone(person1.file)
        sample_content = b'Simple text.'

        with StoreManager(session):
            person1 = Person()
            person1.file = File.create_from(io.BytesIO(sample_content),
                                            content_type='text/plain',
                                            extension='.txt')
            self.assertIsInstance(person1.file, File)
            self.assertEqual(person1.file.locate(), '%s/%s?_ts=%s' % (
                store.public_base_url, person1.file.path, person1.file.timestamp))

    def test_prefix(self):
        prefix = 'test'
        store = _get_os2_store(prefix=prefix)
        StoreManager.register('s3', lambda: store, default=True)

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            file = Column(File.as_mutable(Json))

        session = self.create_all_and_get_session()

        person1 = Person()
        self.assertIsNone(person1.file)
        sample_content = b'Simple text.'

        with StoreManager(session):
            person1 = Person()
            person1.file = File.create_from(io.BytesIO(sample_content),
                                            content_type='text/plain',
                                            extension='.txt')
            self.assertIsInstance(person1.file, File)
            self.assertEqual(person1.file.locate(), '%s/%s?_ts=%s' % (
                store.public_base_url, person1.file.path, person1.file.timestamp))

    def test_public_base_url(self):
        public_base_url = 'http://test.sqlalchemy.media'
        StoreManager.register(
            's3',
            lambda: _get_os2_store(public_base_url=public_base_url),
            default=True
        )

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            file = Column(File.as_mutable(Json))

        session = self.create_all_and_get_session()

        person1 = Person()
        self.assertIsNone(person1.file)
        sample_content = b'Simple text.'

        with StoreManager(session):
            person1 = Person()
            person1.file = File.create_from(io.BytesIO(sample_content),
                                            content_type='text/plain',
                                            extension='.txt')
            self.assertIsInstance(person1.file, File)
            self.assertEqual(person1.file.locate(), '%s/%s?_ts=%s' % (
                public_base_url, person1.file.path, person1.file.timestamp))

    def test_public_base_url_strip(self):
        public_base_url = 'http://test.sqlalchemy.media/'
        StoreManager.register(
            's3',
            lambda: _get_os2_store(public_base_url=public_base_url),
            default=True
        )

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            file = Column(File.as_mutable(Json))

        session = self.create_all_and_get_session()

        person1 = Person()
        self.assertIsNone(person1.file)
        sample_content = b'Simple text.'

        with StoreManager(session):
            person1 = Person()
            person1.file = File.create_from(io.BytesIO(sample_content),
                                            content_type='text/plain',
                                            extension='.txt')
            self.assertIsInstance(person1.file, File)
            self.assertEqual(
                person1.file.locate(),
                '%s/%s?_ts=%s' % (
                    public_base_url.rstrip('/'),
                    person1.file.path,
                    person1.file.timestamp
                )
            )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
