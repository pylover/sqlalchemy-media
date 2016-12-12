import io
import logging
import unittest
from multiprocessing import Process
from os.path import join, dirname, abspath, getsize

import requests
from moto.server import DomainDispatcherApplication, create_backend_app
from werkzeug.serving import run_simple

from sqlalchemy_media.exceptions import S3Error
from sqlalchemy_media.stores import S3Store

TEST_HOST = '127.0.0.1'
TEST_PORT = 10002
TEST_BUCKET = '127'
TEST_ACCESS_KEY = 'test_access_key'
TEST_SECRET_KEY = 'test_secret_key'
TEST_BASE_URL = 'http://{0}:{1}'.format(TEST_HOST, TEST_PORT)


def run_s3_server():
    mock_app = DomainDispatcherApplication(create_backend_app, 's3')
    mock_app.debug = False
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.ERROR)
    [logger.removeHandler(h) for h in logger.handlers]
    run_simple(TEST_HOST, TEST_PORT, mock_app, threaded=True)


class S3StoreTestCase(unittest.TestCase):

    def setUp(self):
        self.server_p = Process(target=run_s3_server)
        self.server_p.daemon = True
        self.server_p.start()

        # create test bucket
        res = requests.put(TEST_BASE_URL)
        assert res.status_code == 200

        self.base_url = 'http://static1.example.orm'
        self.this_dir = abspath(dirname(__file__))
        self.stuff_path = join(self.this_dir, 'stuff')
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def tearDown(self):
        self.server_p.terminate()

    def test_put_from_stream(self):
        store = S3Store(TEST_BUCKET, TEST_ACCESS_KEY, TEST_SECRET_KEY, '')
        store.base_url = TEST_BASE_URL
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)
        length = store.put(target_filename, stream)
        self.assertEqual(length, len(content))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

    def test_delete(self):
        store = S3Store(TEST_BUCKET, TEST_ACCESS_KEY, TEST_SECRET_KEY, '')
        store.base_url = TEST_BASE_URL
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        store.delete(target_filename)
        with self.assertRaises(S3Error):
            store.open(target_filename)

    def test_open(self):
        store = S3Store(TEST_BUCKET, TEST_ACCESS_KEY, TEST_SECRET_KEY, '')
        store.base_url = TEST_BASE_URL
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        # Reading
        with store.open(target_filename, mode='rb') as stored_file, \
                open(self.sample_text_file1, mode='rb') as original_file:
            self.assertEqual(stored_file.read(), original_file.read())


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
