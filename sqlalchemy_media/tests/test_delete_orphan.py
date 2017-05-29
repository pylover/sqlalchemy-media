
import unittest
from io import BytesIO
from os.path import join, exists

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import File, FileList, FileDict, Image
from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.tests.helpers import Json, TempStoreTestCase


class DeleteOrphanTestCase(TempStoreTestCase):

    def setUp(self):
        super().setUp()
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def test_delete_orphan(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            cv = Column(File.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()
        person1 = Person()
        self.assertIsNone(person1.cv)

        with StoreManager(session, delete_orphan=True):
            # First file before commit
            person1.cv = File.create_from(BytesIO(b'Simple text.'), content_type='text/plain', extension='.txt')
            self.assertIsInstance(person1.cv, File)
            first_filename = join(self.temp_path, person1.cv.path)
            self.assertTrue(exists(first_filename))
            person1.cv = File.create_from(BytesIO(b'Second simple text.'))
            second_filename = join(self.temp_path, person1.cv.path)
            self.assertTrue(exists(first_filename))
            self.assertTrue(exists(second_filename))
            session.add(person1)
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertTrue(exists(second_filename))

    def test_without_delete_orphan(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            cv = Column(File.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()
        person1 = Person()

        with StoreManager(session):

            # First file before commit
            person1.cv = File.create_from(BytesIO(b'Simple text.'), content_type='text/plain', extension='.txt')
            first_filename = join(self.temp_path, person1.cv.path)
            person1.cv = File.create_from(BytesIO(b'Second simple text.'))
            second_filename = join(self.temp_path, person1.cv.path)
            session.add(person1)
            session.commit()
            self.assertTrue(exists(first_filename))
            self.assertTrue(exists(second_filename))

    def test_delete_orphan_list(self):
        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            files = Column(FileList.as_mutable(Json))

        session = self.create_all_and_get_session()

        with StoreManager(session, delete_orphan=True):
            person1 = Person()
            person1.files = FileList([
                File.create_from(BytesIO(b'simple text %d' % i)) for i in range(2)
            ])

            # Removing the first file
            first_filename = join(self.temp_path, person1.files[0].path)
            second_filename = join(self.temp_path, person1.files[1].path)

            person1.files = FileList([
                File.create_from(BytesIO(b'New test file: %d' % i)) for i in range(2)
            ])

            session.add(person1)
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertFalse(exists(second_filename))

            first_filename = join(self.temp_path, person1.files[0].path)
            second_filename = join(self.temp_path, person1.files[1].path)
            self.assertTrue(exists(first_filename))
            self.assertTrue(exists(second_filename))

    def test_delete_orphan_list_item(self):
        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            files = Column(FileList.as_mutable(Json))

        session = self.create_all_and_get_session()

        with StoreManager(session, delete_orphan=True):
            person1 = Person()
            person1.files = FileList()
            person1.files.append(File.create_from(BytesIO(b'simple text 1')))
            person1.files.append(File.create_from(BytesIO(b'simple text 2')))
            person1.files.append(File.create_from(BytesIO(b'simple text 3')))

            # Removing the first file
            first_filename = join(self.temp_path, person1.files[0].path)
            person1.files.remove(person1.files[0])
            session.add(person1)
            session.commit()
            self.assertFalse(exists(first_filename))
            # noinspection PyTypeChecker
            self.assertEqual(len(person1.files), 2)

            # Loading from db
            person1 = session.query(Person).one()
            # Preserving the first file's path
            first_filename = join(self.temp_path, person1.files[0].path)

            # remove from orphan list
            f = person1.files[1]
            person1.files.remove(f)
            person1.files.insert(1, f)
            self.assertEqual(len(person1.files), 2)

            # Removing the first file
            del person1.files[0]
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertEqual(len(person1.files), 1)

            old_attachment_filename = join(self.temp_path, person1.files[0].path)
            attachment = person1.files[0].attach(BytesIO(b'Changed inside nested mutable!'))
            attachment_filename = join(self.temp_path, attachment.path)
            self.assertTrue(exists(old_attachment_filename))
            self.assertTrue(exists(attachment_filename))
            session.commit()
            self.assertFalse(exists(old_attachment_filename))
            self.assertTrue(exists(attachment_filename))

    def test_delete_orphan_dict(self):
        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            files = Column(FileDict.as_mutable(Json))

        session = self.create_all_and_get_session()

        with StoreManager(session, delete_orphan=True):
            person1 = Person()
            person1.files = FileDict({
                str(i): File.create_from(BytesIO(b'simple text %d' % i)) for i in range(2)
            })

            # Removing the first file
            first_filename = join(self.temp_path, person1.files['0'].path)
            second_filename = join(self.temp_path, person1.files['1'].path)

            person1.files = FileDict({
                str(i): File.create_from(BytesIO(b'New Text File %d' % i)) for i in range(2)
            })

            session.add(person1)
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertFalse(exists(second_filename))

            first_filename = join(self.temp_path, person1.files['0'].path)
            second_filename = join(self.temp_path, person1.files['1'].path)
            self.assertTrue(exists(first_filename))
            self.assertTrue(exists(second_filename))

    def test_delete_orphan_dict_item(self):
        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            files = Column(FileDict.as_mutable(Json))

        session = self.create_all_and_get_session()

        with StoreManager(session, delete_orphan=True):
            person1 = Person()
            person1.files = FileDict({
                str(i): File.create_from(BytesIO(b'simple text %d' % i)) for i in range(2)
            })

            # Removing the first file
            first_filename = join(self.temp_path, person1.files['0'].path)
            del person1.files['0']
            session.add(person1)
            session.commit()
            self.assertFalse(exists(first_filename))
            # noinspection PyTypeChecker
            self.assertEqual(len(person1.files), 1)

            # Loading from db
            person1 = session.query(Person).one()
            # Preserving the first file's path
            first_filename = join(self.temp_path, person1.files['1'].path)

            # Clearing
            person1.files.clear()
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertEqual(len(person1.files), 0)

    def test_delete_orphan_image(self):
        """
        https://github.com/pylover/sqlalchemy-media/issues/81
        """
        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            pic = Column(Image.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()

        with StoreManager(session, delete_orphan=True):
            person1 = Person()
            person1.pic = Image.create_from(self.cat_jpeg)
            first_filename = join(self.temp_path, person1.pic.path)
            session.commit()
            self.assertTrue(exists(first_filename))

            person1.pic = Image.create_from(self.dog_jpeg)
            session.commit()
            self.assertFalse(exists(first_filename))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
