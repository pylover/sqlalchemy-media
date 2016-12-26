import io
import logging
import unittest
from multiprocessing import Process
from os.path import join, dirname, abspath, getsize

# noinspection PyPackageRequirements
import requests

# noinspection PyPackageRequirements
from moto.server import DomainDispatcherApplication, create_backend_app
from sqlalchemy import Column, Integer

# noinspection PyPackageRequirements
from werkzeug.serving import run_simple

from sqlalchemy_media.attachments import File
from sqlalchemy_media.exceptions import S3Error
from sqlalchemy_media.stores import S3Store
from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.tests.helpers import Json, SqlAlchemyTestCase

TEST_HOST = 'localhost'
TEST_PORT = 10002
TEST_BUCKET = 'test-bucket'
TEST_ACCESS_KEY = 'test_access_key'
TEST_SECRET_KEY = 'test_secret_key'
TEST_REGION = 'ap-northeast-2'
TEST_BASE_URL_FORMAT = 'http://%s:%d/{0}' % (TEST_HOST, TEST_PORT)
TEST_SERVER_URL = TEST_BASE_URL_FORMAT.format(TEST_BUCKET)


def _get_s3_store(bucket=TEST_BUCKET, **kwargs):
    S3Store.BASE_URL_FORMAT = TEST_BASE_URL_FORMAT
    store = S3Store(bucket, TEST_ACCESS_KEY, TEST_SECRET_KEY, TEST_REGION,
                    **kwargs)
    return store


def run_s3_server():  # pragma: no cover
    mock_app = DomainDispatcherApplication(create_backend_app, 's3')
    mock_app.debug = False
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.ERROR)
    [logger.removeHandler(h) for h in logger.handlers]
    run_simple(TEST_HOST, TEST_PORT, mock_app, threaded=True)


class S3StoreTestCase(SqlAlchemyTestCase):

    def setUp(self):
        super(S3StoreTestCase, self).setUp()
        self.server_p = Process(target=run_s3_server)
        self.server_p.daemon = True
        self.server_p.start()

        # create test bucket
        res = requests.put(TEST_SERVER_URL)
        assert res.status_code == 200

        self.base_url = 'http://static1.example.orm'
        self.this_dir = abspath(dirname(__file__))
        self.stuff_path = join(self.this_dir, 'stuff')
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def tearDown(self):
        super(S3StoreTestCase, self).tearDown()
        self.server_p.terminate()

    def test_put_from_stream(self):
        store = _get_s3_store()
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)
        length = store.put(target_filename, stream)
        self.assertEqual(length, len(content))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

    def test_put_error(self):
        store = _get_s3_store(bucket='{0}-2'.format(TEST_BUCKET))
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)

        with self.assertRaises(S3Error):
            store.put(target_filename, stream)

    def test_delete(self):
        store = _get_s3_store()
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        store.delete(target_filename)

        with self.assertRaises(S3Error):
            store.open(target_filename)

    def test_delete_error(self):
        store = _get_s3_store()
        wrong_store = _get_s3_store(bucket='{0}-2'.format(TEST_BUCKET))
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        with self.assertRaises(S3Error):
            wrong_store.delete(target_filename)

    def test_open(self):
        store = _get_s3_store()
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
        StoreManager.register('s3', _get_s3_store, default=True)

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
                TEST_SERVER_URL, person1.file.path, person1.file.timestamp))

    def test_public_base_url(self):
        public_base_url = 'http://test.sqlalchemy.media'
        StoreManager.register(
            's3',
            lambda: _get_s3_store(public_base_url=public_base_url),
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
            lambda: _get_s3_store(public_base_url=public_base_url),
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
