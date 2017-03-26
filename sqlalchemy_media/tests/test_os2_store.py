import io
import unittest
from os.path import join, dirname, abspath, getsize

# noinspection PyPackageRequirements
from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import File
from sqlalchemy_media.exceptions import OS2Error
from sqlalchemy_media.stores import OS2Store
from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.tests.helpers import Json, SqlAlchemyTestCase

TEST_BUCKET = ''
TEST_ACCESS_KEY = ''
TEST_SECRET_KEY = ''
TEST_REGION = ''


def _get_os2_store(bucket=TEST_BUCKET, **kwargs):
    return OS2Store(bucket, TEST_ACCESS_KEY, TEST_SECRET_KEY, TEST_REGION, **kwargs)


class OS2StoreTestCase(SqlAlchemyTestCase):

    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')

        # Pointing to some handy files.
        cls.dog_jpeg = join(cls.stuff_path, 'dog.jpg')

        super(OS2StoreTestCase, cls).setUpClass()

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
