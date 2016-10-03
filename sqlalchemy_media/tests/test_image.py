
import unittest
from os.path import join, exists

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import Image
from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.tests.helpers import Json, TempStoreTestCase


class ImageTestCase(TempStoreTestCase):

    def setUp(self):
        super().setUp()
        self.dog_jpeg = join(self.stuff_path, 'dog.jpg')
        self.cat_jpeg = join(self.stuff_path, 'cat.jpg')

        self.dog_png = join(self.stuff_path, 'dog.png')
        self.cat_png = join(self.stuff_path, 'cat.png')

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
            self.assertEqual(person1.image.extension, '.jpe')
            self.assertTrue(exists(join(self.temp_path, person1.image.path)))

            person1.image = Image.create_from(self.dog_png)
            self.assertEqual(person1.image.content_type, 'image/png')
            self.assertTrue(exists(join(self.temp_path, person1.image.path)))

if __name__ == '__main__':
    unittest.main()
