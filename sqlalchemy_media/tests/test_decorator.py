
import unittest
from os.path import join, exists

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import Image
from sqlalchemy_media.tests.helpers import Json, TempStoreTestCase
from sqlalchemy_media.stores import store_manager


class StoreManagerDecoratorTestCase(TempStoreTestCase):

    def test_decorator(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            image = Column(Image.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()

        person1 = Person()
        self.assertIsNone(person1.image)

        @store_manager(session)
        def add_image():
            person1.image = Image.create_from(self.dog_jpeg)
            self.assertEqual(person1.image.content_type, 'image/jpeg')
            self.assertEqual(person1.image.extension, '.jpg')
            self.assertTrue(exists(join(self.temp_path, person1.image.path)))

            person1.image = Image.create_from(self.dog_png)
            self.assertEqual(person1.image.content_type, 'image/png')
            self.assertTrue(exists(join(self.temp_path, person1.image.path)))

        add_image()


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
