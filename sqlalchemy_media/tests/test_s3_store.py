import argparse
import io
import sys
import unittest
from os.path import join, dirname, abspath, getsize

from sqlalchemy_media.exceptions import S3Error
from sqlalchemy_media.stores import S3Store


class S3StoreTestCase(unittest.TestCase):

    def setUp(self):
        self.bucket = args.s3_bucket
        self.access_key = args.s3_access_key
        self.secret_key = args.s3_secret_key
        self.region = args.s3_region
        self.base_url = 'http://static1.example.orm'
        self.this_dir = abspath(dirname(__file__))
        self.stuff_path = join(self.this_dir, 'stuff')
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def test_put_from_stream(self):
        store = S3Store(self.bucket, self.access_key, self.secret_key,
                        self.region)
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)
        length = store.put(target_filename, stream)
        self.assertEqual(length, len(content))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

    def test_delete(self):
        store = S3Store(self.bucket, self.access_key, self.secret_key,
                        self.region)
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(store.open(target_filename), io.BytesIO)

        store.delete(target_filename)
        with self.assertRaises(S3Error):
            store.open(target_filename)

    def test_open(self):
        store = S3Store(self.bucket, self.access_key, self.secret_key,
                        self.region)
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str, required=True)
    parser.add_argument('--s3-access-key', type=str, required=True)
    parser.add_argument('--s3-secret-key', type=str, required=True)
    parser.add_argument('--s3-region', type=str, required=True)
    args = parser.parse_args()
    del sys.argv[1:]
    unittest.main()
