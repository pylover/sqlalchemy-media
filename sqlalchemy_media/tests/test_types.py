
import unittest
from io import StringIO

from sqlalchemy_media.helpers import is_uri
from sqlalchemy_media.views import AttachmentView, NullAttachmentView
from sqlalchemy_media.types import Attachment


class AttachmentTestCase(unittest.TestCase):

    def test_regex_patterns(self):
        self.assertTrue(is_uri('http://path/to?342=324322&param'))
        self.assertTrue(is_uri('ftp://path/to?342=324322&param'))
        self.assertTrue(is_uri('tcp://path/to?342=324322&param'))
        self.assertTrue(is_uri('protocol://path/to?342=324322&param'))
        self.assertFalse(is_uri('http:/path/to?342=324322&param'))
        self.assertFalse(is_uri('path/to?342=324322&param'))
        self.assertFalse(is_uri('/path/to?342=324322&param'))

    def test_crud(self):
        from sqlalchemy import Column, Integer, create_engine, Unicode
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        engine = create_engine('sqlite:///:memory:', echo=True)
        # engine = create_engine('postgresql://postgres:postgres@localhost/deleteme_jsonb', echo=True)

        class Person(Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            name = Column(Unicode(50), nullable=False, default='person1')
            image = Column(AttachmentView.as_mutable(Attachment), default={'d': 'a'})

            def __repr__(self):
                return "%s %s %s" % (self.id, self.name, self.image)

        Base.metadata.create_all(engine, checkfirst=True)

        session_factory = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=True,
            twophase=False
        )

        # person1 = Person(name='person1')
        person1 = Person()
        self.assertFalse(bool(person1.image))
        self.assertIsInstance(person1.image, NullAttachmentView)
        self.assertFalse(True if person1.image else False)

        text_file = StringIO('Simple text.')
        person1.image.import_(text_file, content_type='text/plain')

        self.assertIsInstance(person1.image, AttachmentView)
        # self.assertNotIsInstance(person1.image, NullAttachmentView)
        # self.assertTrue(bool(person1.image))
        # self.assertTrue(True if person1.image else False)

        # events to create default value in model creation


if __name__ == '__main__':
    unittest.main()



