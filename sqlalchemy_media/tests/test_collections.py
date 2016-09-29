

import unittest
from io import BytesIO
from os.path import join, exists

from sqlalchemy import Column, Integer, Unicode

from sqlalchemy_media import File, StoreManager
from sqlalchemy_media.attachments.collections import FileList
from sqlalchemy_media.tests.helpers import Json, TempStoreTestCase


class CollectionsTestCase(TempStoreTestCase):

    def setUp(self):
        super().setUp()
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def test_file_list(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            name = Column(Unicode(50), nullable=False, default='person1')
            files = Column(FileList.as_mutable(Json), nullable=True)

        session = self.create_all_and_get_session()

        with StoreManager(session):
            person1 = Person()
            person1.files = FileList()
            person1.files.append(File.create_from(BytesIO(b'simple text 1')))
            person1.files.append(File.create_from(BytesIO(b'simple text 2')))
            person1.files.append(File.create_from(BytesIO(b'simple text 3')))
            session.add(person1)
            session.commit()

            person1 = session.query(Person).one()
            for f in person1.files:
                self.assertIsInstance(f, File)
                filename = join(self.temp_path, f.path)
                self.assertTrue(exists(filename))

            # Overwriting the first file
            first_filename = join(self.temp_path, person1.files[0].path)
            person1.files[0].attach(BytesIO(b'Another simple text.'))
            first_new_filename = join(self.temp_path, person1.files[0].path)
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertTrue(exists(first_new_filename))


if __name__ == '__main__':
    unittest.main()
