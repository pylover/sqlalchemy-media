import unittest
import io
from os import makedirs
from os.path import join, dirname, abspath, exists, getsize

from sqlalchemy_media.stores.filesystem import FileSystemStore
from sqlalchemy_media.tests.helpers import simple_http_server


class FileSystemStoreTestCase(unittest.TestCase):

    def setUp(self):
        self.this_dir = abspath(dirname(__file__))
        self.stuff_path = join(self.this_dir, 'stuff')
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')
        self.root_path = join(self.this_dir, 'temp', 'test_filesystem_store')
        if not exists(self.root_path):
            makedirs(self.root_path, exist_ok=True)

    def test_put_from_file(self):
        store = FileSystemStore(self.root_path)

        target_filename = 'test_put_from_file/sample_text_file1.txt'
        length = store.put(target_filename, self.sample_text_file1)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertTrue(exists(join(self.root_path, target_filename)))

    def test_put_from_url(self):
        store = FileSystemStore(self.root_path)
        target_filename = 'test_put_from_url/downloaded_text_file1.txt'
        content = b'Lorem ipsum dolor sit amet'

        with simple_http_server(content) as http_server:
            url = 'http://%s:%s' % http_server.server_address
            length = store.put(target_filename, url)
            self.assertEqual(length, len(content))
            self.assertTrue(exists(join(self.root_path, target_filename)))

    def test_put_from_stream(self):
        store = FileSystemStore(self.root_path)
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)
        length = store.put(target_filename, stream)
        self.assertEqual(length, len(content))
        self.assertTrue(exists(join(self.root_path, target_filename)))


if __name__ == '__main__':
    unittest.main()
