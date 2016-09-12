from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy import Column, Integer, create_engine, Unicode, Index, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json


class JSONEncodedDict(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."

        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()


Base = declarative_base()
# engine = create_engine('postgresql://postgres:postgres@localhost/deleteme_jsonb', echo=True)
engine = create_engine('sqlite:///:memory:', echo=True)


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False, default='vahid')
    image = Column(MutableDict.as_mutable(JSONEncodedDict))

    def __repr__(self):
        return "%s %s %s" % (self.id, self.name, self.image)


if __name__ == '__main__':
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
    person1.image = {'name': 'vahid'}
    print(person1)

    print(person1.image)
