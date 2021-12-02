import io
import unittest
from os.path import join, dirname, abspath, getsize
import functools

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import File, Image as BaseImage, \
    Thumbnail as BaseThumbnail
from sqlalchemy_media.stores import StoreManager, S3Store
from sqlalchemy_media.exceptions import S3Error
from sqlalchemy_media.tests.helpers import (
    TEST_BUCKET,
    Json,
    S3TestCase,
    SqlAlchemyTestCase,
    create_s3_store,
)


class S3StoreTestCase(SqlAlchemyTestCase, S3TestCase):

    @classmethod
    def setUpClass(cls):
        super(S3StoreTestCase, cls).setUpClass()
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')
        cls.dog_jpeg = join(cls.stuff_path, 'dog.jpg')
        cls.sample_text_file1 = join(cls.stuff_path, 'sample_text_file1.txt')

    def test_put_from_stream(self):
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)
        length = self.storage.put(target_filename, stream)
        self.assertEqual(length, len(content))
        self.assertIsInstance(self.storage.open(target_filename), io.BytesIO)

    def test_put_error(self):
        store = create_s3_store(base_url=self.base_url[:-2])
        target_filename = 'test_put_from_stream/file_from_stream1.txt'
        content = b'Lorem ipsum dolor sit amet'
        stream = io.BytesIO(content)

        with self.assertRaises(S3Error):
            store.put(target_filename, stream)

    def test_rrs_put(self):
        StoreManager.register(
            's3',
            functools.partial(create_s3_store, base_url=self.base_url),
            default=True
        )

        class Thumbnail(BaseThumbnail):
            __reproducible__ = True

        class Image(BaseImage):
            __thumbnail_type__ = Thumbnail

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            image = Column(Image.as_mutable(Json))

        session = self.create_all_and_get_session()

        person1 = Person()
        self.assertIsNone(person1.image)

        with StoreManager(session):
            person1 = Person()
            person1.image = Image.create_from(self.dog_jpeg)
            self.assertIsInstance(person1.image, Image)

            thumbnail = person1.image.get_thumbnail(
                width=100,
                auto_generate=True
            )
            self.assertIsInstance(thumbnail, Thumbnail)
            self.assertTrue(thumbnail.reproducible, True)

    def test_delete(self):
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = self.storage.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(self.storage.open(target_filename), io.BytesIO)

        self.storage.delete(target_filename)

        with self.assertRaises(S3Error):
            self.storage.open(target_filename)

    def test_delete_error(self):
        wrong_store = create_s3_store(base_url=self.base_url[:-2])
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = self.storage.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(self.storage.open(target_filename), io.BytesIO)

        with self.assertRaises(S3Error):
            wrong_store.delete(target_filename)

    def test_open(self):
        target_filename = 'test_delete/sample_text_file1.txt'
        with open(self.sample_text_file1, 'rb') as f:
            length = self.storage.put(target_filename, f)
        self.assertEqual(length, getsize(self.sample_text_file1))
        self.assertIsInstance(self.storage.open(target_filename), io.BytesIO)

        # Reading
        with self.storage.open(target_filename, mode='rb') as stored_file, \
                open(self.sample_text_file1, mode='rb') as original_file:
            self.assertEqual(stored_file.read(), original_file.read())

    def test_locate(self):
        StoreManager.register(
            's3',
            functools.partial(create_s3_store, base_url=self.base_url),
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
                    self.base_url, person1.file.path, person1.file.timestamp
                )
            )

    def test_prefix(self):

        prefix = 'test'
        StoreManager.register(
            's3',
            functools.partial(
                create_s3_store, base_url=self.base_url, prefix=prefix),
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
                '%s/%s/%s?_ts=%s' % (
                    self.base_url, prefix, person1.file.path, person1.file.timestamp
                )
            )

    def test_default_base_url(self):
        store = create_s3_store()
        assert store.base_url == 'https://%s.s3.amazonaws.com' % TEST_BUCKET

    def test_public_base_url_strip(self):
        StoreManager.register(
            's3',
            functools.partial(create_s3_store, base_url=self.base_url),
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
                self.base_url, person1.file.path, person1.file.timestamp))

    def test_cdn_url(self):
        cdn_url = 'http//test.sqlalchemy-media.com'
        StoreManager.register(
            's3',
            functools.partial(
                create_s3_store,
                base_url=self.base_url,
                cdn_url=cdn_url
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
            person1.file = File.create_from(
                io.BytesIO(sample_content),
                content_type='text/plain',
                extension='.txt'
            )
            self.assertIsInstance(person1.file, File)
            self.assertEqual(person1.file.locate(), '%s/%s?_ts=%s' % (
                cdn_url, person1.file.path, person1.file.timestamp
            ))

    def test_cdn_url_strip(self):
        cdn_url = 'http//test.sqlalchemy-media.com/'
        StoreManager.register(
            's3',
            functools.partial(
                create_s3_store,
                base_url=self.base_url,
                cdn_url=cdn_url
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
            person1.file = File.create_from(
                io.BytesIO(sample_content),
                content_type='text/plain',
                extension='.txt'
            )
            self.assertIsInstance(person1.file, File)
            self.assertEqual(person1.file.locate(), '%s%s?_ts=%s' % (
                cdn_url, person1.file.path, person1.file.timestamp))

    def test_cdn_url_with_prefix(self):
        prefix = 'media'
        cdn_url = 'http//test.sqlalchemy-media.com'
        StoreManager.register(
            's3',
            functools.partial(
                create_s3_store,
                prefix=prefix,
                base_url=self.base_url,
                cdn_url=cdn_url
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
                cdn_url, prefix, person1.file.path, person1.file.timestamp)
            )

    def test_cdn_url_with_ignore_prefix(self):
        prefix = 'media'
        cdn_url = 'http//test.sqlalchemy-media.com'
        StoreManager.register(
            's3',
            functools.partial(
                create_s3_store,
                prefix=prefix,
                base_url=self.base_url,
                cdn_url=cdn_url,
                cdn_prefix_ignore=True
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
            person1.file = File.create_from(
                io.BytesIO(sample_content),
                content_type='text/plain',
                extension='.txt'
            )
            self.assertIsInstance(person1.file, File)
            self.assertEqual(
                person1.file.locate(), '%s/%s?_ts=%s' % (
                    cdn_url,
                    person1.file.path,
                    person1.file.timestamp
                )
            )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
