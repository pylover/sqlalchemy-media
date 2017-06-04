
import time
import unittest
import io
import shutil
from os import makedirs
from os.path import join, exists, getsize

from sqlalchemy_media.stores import SSHStore
from sqlalchemy_media.tests.helpers import MockupSSHTestCase


class SSHStoreTestCase(MockupSSHTestCase):
    def setUp(self):
        super().setUp()
        self.base_url = 'http://static1.example.orm'
        self.stuff_path = join(self.here, 'stuff')
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def create_ssh_store(self):
        path = join(self.temp_path)
        if exists(path):
            shutil.rmtree(self.temp_path)
        makedirs(path)
        s = SSHStore(self.create_ssh_client(), self.temp_path, self.base_url)
        return s

    def test_put_from_stream(self):
        store = self.create_ssh_store()
        # target_filename = 'a/b/c/file_from_stream1.txt'
        target_filename = 'file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)
        length = store.put(target_filename, stream)
        self.assertEqual(length, len(content))
        self.assertTrue(exists(join(self.temp_path, target_filename)))

    def test_delete(self):
        store = self.create_ssh_store()
        target_filename = 'sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            store.put(target_filename, f)

        store.delete(target_filename)
        self.assertFalse(exists(join(self.temp_path, target_filename)))

    def test_open(self):
        store = self.create_ssh_store()
        target_filename = 'sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertTrue(exists(join(self.temp_path, target_filename)))

        # Reading
        with store.open(target_filename, mode='rb') as stored_file, \
                open(self.sample_text_file1, mode='rb') as original_file:
            self.assertEqual(stored_file.read(), original_file.read())

        # Writing
        new_content = b'Some Binary Data'
        with store.open(target_filename, mode='wb') as stored_file:
            stored_file.write(new_content)

        with store.open(target_filename, mode='rb') as stored_file:
            self.assertEqual(stored_file.read(), new_content)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()