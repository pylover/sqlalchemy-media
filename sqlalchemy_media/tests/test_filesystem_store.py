import unittest
from os import makedirs
from os.path import join, dirname, abspath, exists


from sqlalchemy_media.stores.filesystem import FileSystemStore


class FileSystemStoreTestCase(unittest.TestCase):

    def setUp(self):
        self.this_dir = abspath(dirname(__file__))
        self.stuff_path = join(self.this_dir, 'stuff', 'test_filesystem_store')
        self.root_path = join(self.this_dir, 'temp', 'test_filesystem_store')
        if not exists(self.root_path):
            makedirs(self.root_path, exist_ok=True)

    def test_put_delete(self):
        store = FileSystemStore(self.root_path)

        # put with filename

        # put with stream

        # put with cgi storage

        # put with url


if __name__ == '__main__':
    unittest.main()
