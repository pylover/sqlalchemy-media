

import unittest
from io import BytesIO
from os.path import join, exists

from sqlalchemy import Column, Integer, Unicode

from sqlalchemy_media import File, StoreManager
from sqlalchemy_media.attachments.collections import FileList
from sqlalchemy_media.tests.helpers import Json, TempStoreTestCase
from sqlalchemy_media.exceptions import MaximumLengthIsReachedError, MinimumLengthIsNotReachedError


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
            pass


if __name__ == '__main__':
    unittest.main()
