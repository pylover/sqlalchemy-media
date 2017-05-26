
import unittest
from os.path import join, exists

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import Image, Thumbnail, ImageList
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

    def test_thumbnail_delete(self):
        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            image = Column(Image.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()

        # person1 = Person(name='person1')
        person1 = Person()
        self.assertIsNone(person1.image)

        with StoreManager(session, delete_orphan=True):
            person1.image = Image.create_from(self.dog_jpeg)
            session.add(person1)
            session.commit()

            thumbnail = person1.image.get_thumbnail(width=100, auto_generate=True)
            self.assertIsInstance(thumbnail, Thumbnail)

            image_filename = join(self.temp_path, person1.image.path)
            self.assertTrue(exists(image_filename))

            first_thumbnail_filename = join(self.temp_path, thumbnail.path)
            self.assertTrue(exists(first_thumbnail_filename))

            session.delete(person1)
            session.commit()
            self.assertFalse(exists(image_filename))
            self.assertFalse(exists(first_thumbnail_filename))

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

    def test_image_thumbnail_pre_generate(self):
        """
        Issue #72
        :return:
        """
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
            person1.image.generate_thumbnail(width=100)

            session.add(person1)
            session.commit()

        session = self.create_all_and_get_session()
        person1 = session.query(Person).filter(Person.id == person1.id).one()
        with StoreManager(session):
            self.assertTrue(person1.image.locate().startswith('http://static1.example.orm/images/image-'))
            thumbnail = person1.image.get_thumbnail(width=100)
            self.assertTrue(thumbnail.locate().startswith('http://static1.example.orm/thumbnails/thumbnail-'))

    def test_image_list(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            images = Column(ImageList.as_mutable(Json))

        session = self.create_all_and_get_session()

        with StoreManager(session, delete_orphan=True):
            person1 = Person()
            person1.images = ImageList()
            person1.images.append(Image.create_from(self.dog_jpeg))
            person1.images.append(Image.create_from(self.cat_jpeg))
            session.add(person1)
            session.commit()

            person1 = session.query(Person).one()
            self.assertEqual(len(person1.images), 2)
            for f in person1.images:
                self.assertIsInstance(f, Image)
                filename = join(self.temp_path, f.path)
                self.assertTrue(exists(filename))
                self.assertEqual(f.locate(), '%s/%s?_ts=%s' % (self.base_url, f.path, f.timestamp))

            # Overwriting the first image
            first_filename = join(self.temp_path, person1.images[0].path)
            person1.images[0].attach(self.dog_png)
            first_new_filename = join(self.temp_path, person1.images[0].path)
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertTrue(exists(first_new_filename))

            person1 = session.query(Person).one()
            # Generating a thumbnail for the first image
            thumbnail = person1.images[0].get_thumbnail(width=10, auto_generate=True)
            session.commit()
            thumbnail_filename = join(self.temp_path, thumbnail.path)
            self.assertTrue(exists(thumbnail_filename))

            # Removing the image should force to orphanage the thumbnails.
            del person1.images[0]
            session.commit()
            self.assertFalse(exists(thumbnail_filename))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
