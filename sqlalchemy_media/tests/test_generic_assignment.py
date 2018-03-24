import unittest
import io
from os.path import join, exists

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import File
from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.tests.helpers import Json, TempStoreTestCase


class AutoCoerceFile(File):
    __auto_coercion__ = True


class GenericAssignmentTestCase(TempStoreTestCase):

    def test_file_assignment(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            cv = Column(AutoCoerceFile.as_mutable(Json))

        session = self.create_all_and_get_session()
        person1 = Person()
        resume = io.BytesIO(b'This is my resume')
        with StoreManager(session):
            person1.cv = resume
            self.assertIsNone(person1.cv.content_type)
            self.assertIsNone(person1.cv.extension)
            self.assertTrue(exists(join(self.temp_path, person1.cv.path)))

            person1.cv = resume, 'text/plain'
            self.assertEqual(person1.cv.content_type, 'text/plain')
            self.assertEqual(person1.cv.extension, '.txt')
            self.assertTrue(exists(join(self.temp_path, person1.cv.path)))

            person1.cv = resume, 'text/plain', 'myfile.note'
            self.assertEqual(person1.cv.content_type, 'text/plain')
            self.assertEqual(person1.cv.extension, '.note')
            self.assertTrue(exists(join(self.temp_path, person1.cv.path)))



if __name__ == '__main__':  # pragma: no cover
    unittest.main()

