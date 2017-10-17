
import unittest
import io
from os.path import join, getsize, abspath, dirname

from sqlalchemy_media.stores import FTPStore
from sqlalchemy_media.tests.helpers import MockFTP, SqlAlchemyTestCase


class FTPStoreTestCase(SqlAlchemyTestCase):
    def setUp(self):
        super().setUp()
        self.here = abspath(join(dirname(__file__), '.'))
        self.base_url = 'http://static1.example.orm/'
        self.stuff_path = join(self.here, 'stuff')
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')
        self.root_path = '/'

    def create_ftp_store(self):
        self.ftp_connection = MockFTP()
        return (
            self.ftp_connection,
            FTPStore(self.ftp_connection, self.root_path, self.base_url),
        )

    def test_put_from_stream(self):
        ftp_connection, store = self.create_ftp_store()
        target_filename = 'file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)
        length = store.put(target_filename, stream)
        self.assertEqual(length, len(content))

        # make directories
        ftp_connection._exists = False
        target_filename = 'a/b/c/file_from_stream1.txt'
        stream = io.BytesIO(content)
        length = store.put(target_filename, stream)
        self.assertEqual(length, len(content))

    def test_delete(self):
        ftp_connection, store = self.create_ftp_store()
        store.delete('remote_file.txt')
        ftp_connection._set_exists(False)
        with self.assertRaises(Exception):
            store.delete('photos/nature/remote.txt')

    def test_open(self):
        ftp_connection, store = self.create_ftp_store()
        target_filename = 'sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = store.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        # self.assertTrue(exists(join(self.temp_path, target_filename)))

        # Reading
        with open(self.sample_text_file1, 'rb') as mock_contents:
            ftp_connection._set_contents(mock_contents.read())

        with store.open(target_filename, mode='rb') as stored_file, \
                open(self.sample_text_file1, mode='rb') as original_file:
            self.assertEqual(stored_file.read(), original_file.read())

    def test_locate(self):
        import functools
        from sqlalchemy import Column, Integer
        from sqlalchemy_media import File, StoreManager
        from sqlalchemy_media.tests.helpers.types import Json
        StoreManager.register(
            'ftp',
            functools.partial(FTPStore, hostname=MockFTP(), root_path=self.root_path, base_url=self.base_url),
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
                '%s%s?_ts=%s' % (
                    self.base_url,
                    person1.file.path,
                    person1.file.timestamp
                )
            )

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
