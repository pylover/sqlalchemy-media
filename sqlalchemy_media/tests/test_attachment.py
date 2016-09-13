
import unittest
from io import StringIO
import json

from sqlalchemy import Column, Integer, create_engine, Unicode, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_media.models import Attachment, NullAttachment


# noinspection PyAbstractClass
class Json(TypeDecorator):
    impl = Unicode

    def process_bind_param(self, value, engine):
        return json.dumps(value)

    def process_result_value(self, value, engine):
        if value is None:
            return None

        return json.loads(value)


class AttachmentTestCase(unittest.TestCase):

    def test_attachment(self):

        Base = declarative_base()

        engine = create_engine('sqlite:///:memory:', echo=True)
        # engine = create_engine('postgresql://postgres:postgres@localhost/deleteme_jsonb', echo=True)

        class Person(Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            name = Column(Unicode(50), nullable=False, default='person1')
            image = Column(Attachment.as_mutable(Json), default={'d': 'a'})

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
        self.assertIsInstance(person1.image, NullAttachment)
        self.assertFalse(True if person1.image else False)

        person1.image.attach(StringIO('Simple text.'), content_type='text/plain')

        self.assertIsInstance(person1.image, Attachment)
        # self.assertNotIsInstance(person1.image, NullAttachmentView)
        # self.assertTrue(bool(person1.image))
        # self.assertTrue(True if person1.image else False)

        # events to create default value in model creation


if __name__ == '__main__':
    unittest.main()



