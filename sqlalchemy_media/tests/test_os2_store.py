import functools
import io
import unittest
from os.path import join, dirname, abspath, getsize

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import File
from sqlalchemy_media.exceptions import OS2Error
from sqlalchemy_media.stores import OS2Store
from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.tests.helpers import Json, SqlAlchemyTestCase, mockup_os2_server


TEST_BUCKET = 'sa-media-test'
TEST_ACCESS_KEY = 'sa-media-ak'
TEST_SECRET_KEY = 'sa-media-sk'
TEST_REGION = 'sa-media'


def create_os2_store(server, bucket=TEST_BUCKET, **kwargs):
    base_headers = {'HOST': '%s.oss-%s.localhost:%s' % (bucket, TEST_REGION, server.server_address[1])}
    return OS2Store(bucket, TEST_ACCESS_KEY, TEST_SECRET_KEY, TEST_REGION, base_headers=base_headers, **kwargs)


class OS2StoreTestCase(SqlAlchemyTestCase):

    @classmethod
    def setUpClass(cls):
        super(OS2StoreTestCase, cls).setUpClass()
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')
        cls.dog_jpeg = join(cls.stuff_path, 'dog.jpg')
        cls.temp_path = join(cls.this_dir, 'temp', cls.__name__)
        cls.base_url = 'http://static1.example.orm'
        cls.sample_text_file1 = join(cls.stuff_path, 'sample_text_file1.txt')

    def test_put_from_stream(self):
        with mockup_os2_server(self.temp_path, TEST_BUCKET) as (server, url):
            store = create_os2_store(server, base_url=url)
            target_filename = 'test_put_from_stream/file_from_stream1.txt'
            content = b'Lorem ipsum dolor sit amet'
            stream = io.BytesIO(content)
            length = store.put(target_filename, stream)
            self.assertEqual(length, len(content))
            self.assertIsInstance(store.open(target_filename), io.BytesIO)

    def test_put_error(self):
        with mockup_os2_server(self.temp_path, TEST_BUCKET) as (server, url):
            store = create_os2_store(server, bucket=TEST_BUCKET[:-2], base_url=url)
            target_filename = 'test_put_from_stream/file_from_stream1.txt'
            content = b'Lorem ipsum dolor sit amet'
            stream = io.BytesIO(content)
            with self.assertRaises(OS2Error):
                store.put(target_filename, stream)

    def test_delete(self):
        with mockup_os2_server(self.temp_path, TEST_BUCKET) as (server, url):
            store = create_os2_store(server, base_url=url)
            target_filename = 'test_delete/sample_text_file1.txt'

            with open(self.sample_text_file1, 'rb') as f:
                length = store.put(target_filename, f)

            self.assertEqual(length, getsize(self.sample_text_file1))
            self.assertIsInstance(store.open(target_filename), io.BytesIO)
            store.delete(target_filename)

            with self.assertRaises(OS2Error):
                store.open(target_filename)

    def test_delete_error(self):
        with mockup_os2_server(self.temp_path, TEST_BUCKET) as (server, url):
            store = create_os2_store(server, base_url=url)
            wrong_store = create_os2_store(server, base_url=url, bucket=TEST_BUCKET[:-2])
            target_filename = 'test_delete/sample_text_file1.txt'
            with open(self.sample_text_file1, 'rb') as f:
                length = store.put(target_filename, f)
            self.assertEqual(length, getsize(self.sample_text_file1))
            self.assertIsInstance(store.open(target_filename), io.BytesIO)

            with self.assertRaises(OS2Error):
                wrong_store.delete(target_filename)

    def test_open(self):
        with mockup_os2_server(self.temp_path, TEST_BUCKET) as (server, url):
            store = create_os2_store(server, base_url=url)
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
        with mockup_os2_server(self.temp_path, TEST_BUCKET) as (server, url):
            StoreManager.register('os2', functools.partial(create_os2_store, server, base_url=url), default=True)

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
                person1.file = File.create_from(io.BytesIO(sample_content), content_type='text/plain', extension='.txt')
                self.assertIsInstance(person1.file, File)
                self.assertEqual(
                    person1.file.locate(),
                    '%s/%s?_ts=%s' % (
                        url,
                        person1.file.path,
                        person1.file.timestamp
                    )
                )

    def test_prefix(self):
        with mockup_os2_server(self.temp_path, TEST_BUCKET) as (server, url):
            prefix = 'test'
            StoreManager.register(
                'os2',
                functools.partial(
                    create_os2_store, server, base_url=url, prefix=prefix
                ),
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
                self.assertEqual(person1.file.locate(), '%s/%s/%s?_ts=%s' % (
                    url,
                    prefix,
                    person1.file.path,
                    person1.file.timestamp
                ))

    def test_public_base_url(self):
        with mockup_os2_server(self.temp_path, TEST_BUCKET) as (server, url):
            StoreManager.register(
                'os2',
                functools.partial(create_os2_store, server, base_url=url),
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
                    url, person1.file.path, person1.file.timestamp))

    def test_public_base_url_strip(self):
        with mockup_os2_server(self.temp_path, TEST_BUCKET) as (server, url):
            StoreManager.register(
                'os2',
                functools.partial(create_os2_store, server, base_url=url),
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
                        url.rstrip('/'),
                        person1.file.path,
                        person1.file.timestamp
                    )
                )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
