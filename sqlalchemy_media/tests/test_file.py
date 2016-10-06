
import unittest
from io import BytesIO
from os.path import join, exists

from sqlalchemy import Column, Integer

from sqlalchemy_media import File, StoreManager, ContentTypeValidator, MagicAnalyzer
from sqlalchemy_media.tests.helpers import Json, TempStoreTestCase
from sqlalchemy_media.exceptions import MaximumLengthIsReachedError, MinimumLengthIsNotReachedError, \
    ContentTypeValidationError


class FileTestCase(TempStoreTestCase):

    def setUp(self):
        super().setUp()
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def test_file(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            cv = Column(File.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()

        # person1 = Person(name='person1')
        person1 = Person()
        self.assertIsNone(person1.cv)
        sample_content = b'Simple text.'

        with StoreManager(session):

            # First file before commit
            person1.cv = File.create_from(BytesIO(sample_content), content_type='text/plain', extension='.txt')
            self.assertIsInstance(person1.cv, File)
            self.assertEqual(person1.cv.locate(), '%s/%s?_ts=%s' % (
                self.base_url, person1.cv.path, person1.cv.timestamp))
            self.assertDictEqual(person1.cv, {
                'content_type': 'text/plain',
                'key': person1.cv.key,
                'extension': '.txt',
                'length': len(sample_content),
                'timestamp': person1.cv.timestamp
            })
            first_filename = join(self.temp_path, person1.cv.path)
            self.assertTrue(exists(first_filename))
            self.assertEqual(person1.cv.length, len(sample_content))

            # Second file before commit
            person1.cv.attach(BytesIO(sample_content), content_type='text/plain', extension='.txt')
            second_filename = join(self.temp_path, person1.cv.path)
            self.assertTrue(exists(second_filename))

            # Adding object to session, the new life-cycle of the person1 just began.
            session.add(person1)
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertTrue(exists(second_filename))

            # Loading again
            sample_content = b'Lorem ipsum dolor sit amet'
            person1 = session.query(Person).filter(Person.id == person1.id).one()
            person1.cv.attach(BytesIO(sample_content), content_type='text/plain', extension='.txt')
            self.assertIsInstance(person1.cv, File)
            self.assertDictEqual(person1.cv, {
                'content_type': 'text/plain',
                'key': person1.cv.key,
                'extension': '.txt',
                'length': len(sample_content),
                'timestamp': person1.cv.timestamp
            })
            third_filename = join(self.temp_path, person1.cv.path)
            self.assertTrue(exists(second_filename))
            self.assertTrue(exists(third_filename))

            # Committing the session, so the store must done the scheduled jobs
            session.commit()
            self.assertFalse(exists(second_filename))
            self.assertTrue(exists(third_filename))

            # Rollback
            person1.cv.attach(BytesIO(sample_content), content_type='text/plain', extension='.txt')
            forth_filename = join(self.temp_path, person1.cv.path)
            self.assertTrue(exists(forth_filename))
            session.rollback()
            self.assertTrue(exists(third_filename))
            self.assertFalse(exists(forth_filename))

            # Delete file after object deletion
            person1 = session.query(Person).filter(Person.id == person1.id).one()
            session.delete(person1)
            session.commit()
            self.assertFalse(exists(third_filename))

            # Delete file on set to null
            person1 = Person()
            self.assertIsNone(person1.cv)
            person1.cv = File()
            person1.cv.attach(BytesIO(sample_content), content_type='text/plain', extension='.txt')
            fifth_filename = join(self.temp_path, person1.cv.path)
            person1.cv = None
            session.add(person1)
            self.assertTrue(exists(fifth_filename))
            session.commit()
            # Because delete_orphan is not set.
            self.assertTrue(exists(fifth_filename))

            # storing a file on separate store:
            person1.cv = File.create_from(BytesIO(sample_content), store_id='temp_fs')
            fifth_filename = join(self.sys_temp_path, person1.cv.path)
            session.commit()
            self.assertTrue(exists(fifth_filename))

    def test_file_size_limit(self):

        class LimitedFile(File):
            __min_length__ = 20
            __max_length__ = 30

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            cv = Column(LimitedFile.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()

        person1 = Person()
        person1.cv = LimitedFile()

        with StoreManager(session):

            # MaximumLengthIsReachedError, MinimumLengthIsNotReachedError
            self.assertRaises(MinimumLengthIsNotReachedError, person1.cv.attach, BytesIO(b'less than 20 chars!'))
            self.assertRaises(MaximumLengthIsReachedError, person1.cv.attach,
                              BytesIO(b'more than 30 chars!............'))

    def test_attribute_type_assertion(self):
        class MyAttachmentType(File):
            pass

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            cv = Column(MyAttachmentType.as_mutable(Json), nullable=True)

        person1 = Person()

        def set_invalid_type():
            person1.cv = File()

        def set_invalid_type_via_constructor():
            Person(cv=File())

        self.assertRaises(TypeError, set_invalid_type)
        self.assertRaises(TypeError, set_invalid_type_via_constructor)

    def test_model_constructor(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            cv = Column(File.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()
        person1 = Person(cv=File())
        self.assertIsInstance(person1.cv, File)
        with StoreManager(session):
            person1.cv.attach(BytesIO(b'Simple text'))
            session.add(person1)
            session.commit()

    def test_overwrite(self):
        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            cv = Column(File.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()
        person1 = Person(cv=File())
        self.assertIsInstance(person1.cv, File)
        with StoreManager(session):
            person1.cv.attach(BytesIO(b'Simple text'))
            cv_filename = join(self.temp_path, person1.cv.path)
            self.assertTrue(exists(cv_filename))
            session.add(person1)
            session.commit()

            # Now overwriting the file
            person1 = session.query(Person).filter(Person.id == person1.id).one()
            person1.cv.attach(BytesIO(b'Another simple text'), overwrite=True)
            self.assertTrue(exists(cv_filename))
            session.commit()
            self.assertTrue(exists(cv_filename))

    def test_content_type_validator(self):

        class PDFFile(File):
            __pre_processors__ = [
                MagicAnalyzer(),
                ContentTypeValidator(['application/pdf', 'image/jpeg'])
            ]

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            cv = Column(PDFFile.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()
        person1 = Person(cv=PDFFile())
        with StoreManager(session):
            self.assertIsNotNone(person1.cv.attach(self.cat_jpeg))
            self.assertRaises(ContentTypeValidationError, person1.cv.attach, BytesIO(b'Simple text'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
