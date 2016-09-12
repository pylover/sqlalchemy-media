import unittest
from os import makedirs
from os.path import join, dirname, abspath, exists, getsize


from sqlalchemy_media.stores.filesystem import FileSystemStore


class FileSystemStoreTestCase(unittest.TestCase):

    def setUp(self):
        self.this_dir = abspath(dirname(__file__))
        self.stuff_path = join(self.this_dir, 'stuff')
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')
        self.root_path = join(self.this_dir, 'temp', 'test_filesystem_store')
        if not exists(self.root_path):
            makedirs(self.root_path, exist_ok=True)

    def test_put_delete(self):
        store = FileSystemStore(self.root_path)

        # put with filename
        target_filename = 'test_put_delete/sample_text_file1.txt'
        length = store.put(target_filename, self.sample_text_file1)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertTrue(exists(join(self.root_path, target_filename)))

        # put with stream

        # put with cgi storage

        # put with url


if __name__ == '__main__':
    unittest.main()
