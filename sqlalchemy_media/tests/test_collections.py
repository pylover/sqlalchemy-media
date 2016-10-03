
import unittest
from io import BytesIO
from os.path import join, exists

from sqlalchemy import Column, Integer

from sqlalchemy_media.attachments import File, FileList, FileDict, AttachmentList, AttachmentDict
from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.tests.helpers import Json, TempStoreTestCase


class CollectionsTestCase(TempStoreTestCase):

    def setUp(self):
        super().setUp()
        self.sample_text_file1 = join(self.stuff_path, 'sample_text_file1.txt')

    def test_attachment_list(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            files = Column(FileList.as_mutable(Json))

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
            self.assertEqual(len(person1.files), 3)
            for f in person1.files:
                self.assertIsInstance(f, File)
                filename = join(self.temp_path, f.path)
                self.assertTrue(exists(filename))
                self.assertEqual(f.locate(), '%s/%s?_ts=%s' % (self.base_url, f.path, f.timestamp))

            # Overwriting the first file
            first_filename = join(self.temp_path, person1.files[0].path)
            person1.files[0].attach(BytesIO(b'Another simple text.'))
            first_new_filename = join(self.temp_path, person1.files[0].path)
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertTrue(exists(first_new_filename))

            # pop
            self.assertIsNotNone(person1.files.pop())

            # extend
            person1.files.extend([
                File.create_from(BytesIO(b'simple text 4')),
                File.create_from(BytesIO(b'simple text 5'))
            ])
            self.assertEqual(len(person1.files), 4)

            # insert
            person1.files.insert(2, File.create_from(BytesIO(b'simple text 3 # restored')))
            self.assertEqual(len(person1.files), 5)

            # __setitem__
            old_key = person1.files[3].key
            person1.files[3] = File.create_from(BytesIO(b'simple text 4 # replaced'))
            self.assertEqual(len(person1.files), 5)
            self.assertNotEqual(person1.files[3].key, old_key)

            # __setslice__
            old_keys = [a.key for a in person1.files[2:4]]
            person1.files[2:4] = [
                File.create_from(BytesIO(b'simple text 4')),
                File.create_from(BytesIO(b'simple text 5'))
            ]
            self.assertEqual(len(person1.files), 5)
            for i, a in enumerate(person1.files[2:4]):
                self.assertNotEqual(a.key, old_keys[i])

            # clear
            person1.files.clear()
            self.assertEqual(len(person1.files), 0)

    def test_coerce(self):

        self.assertRaises(ValueError, AttachmentList.coerce, 'cv', 10)  # non-iterable
        self.assertIsInstance(AttachmentList.coerce('cv', AttachmentList()), AttachmentList)  # same type

        self.assertRaises(ValueError, AttachmentDict.coerce, 'cv', 10)  # non-iterable
        self.assertIsInstance(AttachmentDict.coerce('cv', AttachmentDict()), AttachmentDict)  # same type

    def test_file_dict(self):

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            files = Column(FileDict.as_mutable(Json))

        session = self.create_all_and_get_session()

        with StoreManager(session):
            person1 = Person()
            person1.files = FileDict()
            person1.files['first'] = File.create_from(BytesIO(b'simple text 1'))
            person1.files['second'] = File.create_from(BytesIO(b'simple text 2'))
            person1.files['third'] = File.create_from(BytesIO(b'simple text 3'))
            session.add(person1)
            session.commit()

            person1 = session.query(Person).one()
            self.assertEqual(len(person1.files), 3)
            for f in person1.files.values():
                self.assertIsInstance(f, File)
                filename = join(self.temp_path, f.path)
                self.assertTrue(exists(filename))

            # Overwriting the first file
            first_filename = join(self.temp_path, person1.files['first'].path)
            person1.files['first'].attach(BytesIO(b'Another simple text.'))
            first_new_filename = join(self.temp_path, person1.files['first'].path)
            session.commit()
            self.assertFalse(exists(first_filename))
            self.assertTrue(exists(first_new_filename))

            # setdefault
            person1.files.setdefault('default', File.create_from(BytesIO(b'Default file')))
            self.assertIn('default', person1.files)

            # update
            person1.files.update(dict(
                edit1=File.create_from(BytesIO(b'Updated file 1')),
                edit2=File.create_from(BytesIO(b'Updated file 2'))
            ))
            self.assertIn('edit1', person1.files)
            self.assertIn('edit2', person1.files)

            # pop
            self.assertEqual(len(person1.files), 6)
            self.assertIsNotNone(person1.files.pop('first'))
            self.assertEqual(len(person1.files), 5)

            # popitem
            self.assertEqual(len(person1.files), 5)
            self.assertIsNotNone(person1.files.popitem())
            self.assertEqual(len(person1.files), 4)

            # setitem
            person1.files['setitem'] = File.create_from(BytesIO(b'setitem file'))
            self.assertIn('setitem', person1.files)
            self.assertEqual(len(person1.files), 5)

            # delitem
            del person1.files['setitem']
            self.assertEqual(len(person1.files), 4)

            # clear
            person1.files.clear()
            self.assertEqual(len(person1.files), 0)

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
