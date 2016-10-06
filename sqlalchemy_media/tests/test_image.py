
import unittest
from os.path import join, exists

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import Image, Thumbnail
from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.tests.helpers import Json, TempStoreTestCase
from sqlalchemy_media.exceptions import ThumbnailIsNotAvailableError
from sqlalchemy_media.processors import ImageProcessor


class ImageTestCase(TempStoreTestCase):

    def test_image(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            image = Column(Image.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()

        # person1 = Person(name='person1')
        person1 = Person()
        self.assertIsNone(person1.image)

        with StoreManager(session):
            person1.image = Image.create_from(self.dog_jpeg)
            self.assertEqual(person1.image.content_type, 'image/jpeg')
            self.assertEqual(person1.image.extension, '.jpg')
            self.assertTrue(exists(join(self.temp_path, person1.image.path)))

            person1.image = Image.create_from(self.dog_png)
            self.assertEqual(person1.image.content_type, 'image/png')
            self.assertTrue(exists(join(self.temp_path, person1.image.path)))

    def test_thumbnail(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            image = Column(Image.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()

        # person1 = Person(name='person1')
        person1 = Person()
        self.assertIsNone(person1.image)

        with StoreManager(session):
            person1.image = Image.create_from(self.dog_jpeg)

            # Getting an unavailable thumbnail.
            self.assertRaises(ThumbnailIsNotAvailableError, person1.image.get_thumbnail, width=100)

            # Auto generate
            thumbnail = person1.image.get_thumbnail(width=100, auto_generate=True)
            self.assertIsInstance(thumbnail, Thumbnail)

            self.assertEqual(thumbnail.content_type, 'image/jpeg')
            self.assertEqual(thumbnail.extension, '.jpg')
            self.assertEqual(thumbnail.width, 100)
            self.assertEqual(thumbnail.height, 75)
            first_thumbnail_filename = join(self.temp_path, thumbnail.path)
            self.assertTrue(exists(first_thumbnail_filename))
            self.assertIsNotNone(person1.image.get_thumbnail(width=100))
            self.assertIsNotNone(person1.image.get_thumbnail(height=75))

            # Generate thumbnail with height
            thumbnail = person1.image.generate_thumbnail(height=20)
            self.assertEqual(thumbnail.width, 26)
            second_thumbnail_filename = join(self.temp_path, thumbnail.path)
            self.assertTrue(exists(second_thumbnail_filename))
            self.assertIsNotNone(person1.image.get_thumbnail(width=26))
            self.assertIsNotNone(person1.image.get_thumbnail(height=20))

            # Generate thumbnail with ratio
            thumbnail = person1.image.generate_thumbnail(ratio=1/3)
            self.assertEqual(thumbnail.width, 213)
            self.assertEqual(thumbnail.height, 160)
            third_thumbnail_filename = join(self.temp_path, thumbnail.path)
            self.assertTrue(exists(third_thumbnail_filename))
            self.assertIsNotNone(person1.image.get_thumbnail(ratio=1/3))
            self.assertIsNotNone(person1.image.get_thumbnail(width=213))
            self.assertIsNotNone(person1.image.get_thumbnail(height=160))

            # Exceptions
            self.assertRaises(ValueError, person1.image.generate_thumbnail)
            self.assertRaises(ValueError, person1.image.generate_thumbnail, width=10, height=10)
            self.assertRaises(ValueError, person1.image.generate_thumbnail, width=10, ratio=.1)
            self.assertRaises(ValueError, person1.image.generate_thumbnail, height=10, ratio=.1)
            self.assertRaises(ValueError, person1.image.generate_thumbnail, ratio=1.1)
            self.assertRaises(ValueError, person1.image.generate_thumbnail, width=0)
            self.assertRaises(ValueError, person1.image.generate_thumbnail, height=0)

            self.assertRaises(TypeError, person1.image.generate_thumbnail, width='a')
            self.assertRaises(TypeError, person1.image.generate_thumbnail, height='a')
            self.assertRaises(TypeError, person1.image.generate_thumbnail, ratio='a')

        # Attaching new image must deletes all thumbnails: issue: #54
        with StoreManager(session):
            person1.image.attach(self.cat_png)
            session.commit()
            self.assertFalse(exists(first_thumbnail_filename))
            self.assertFalse(exists(second_thumbnail_filename))
            self.assertFalse(exists(third_thumbnail_filename))

    def test_pre_process(self):

        class Banner(Image):
            __pre_processors__ = ImageProcessor(fmt='jpeg', width=300)

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            image = Column(Banner.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()

        # person1 = Person(name='person1')
        person1 = Person()
        self.assertIsNone(person1.image)

        with StoreManager(session):
            person1.image = Banner.create_from(self.cat_png)
            self.assertEqual(person1.image.content_type, 'image/jpeg')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
