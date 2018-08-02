from typing import Iterable
import json

from sqlalchemy import Column, TypeDecorator, VARCHAR, Integer, create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=False)
session_factory = sessionmaker(bind=engine)


class JSONEncodedDict(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class Image(MutableDict):

    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionary to instance of this class."""
        if not isinstance(value, cls):
            if isinstance(value, dict):
                return cls(value)
            return super().coerce(key, value)
        else:
            return value

    def changed(self):
        super().changed()


class ImageList(MutableList):
    __item_type__ = Image

    def observe_item(self, item):
        item = self.__item_type__.coerce(None, item)
        item._parents = self._parents
        return item

    def __setitem__(self, index, value):
        """Detect list set events and emit change events."""
        list.__setitem__(self, index, self.observe_item(value))
        self.changed()

    def __setslice__(self, start, end, value):
        """Detect list set events and emit change events."""
        list.__setslice__(self, start, end, [self.observe_item(i) for i in value])
        self.changed()

    def append(self, x):
        list.append(self, self.observe_item(x))
        self.changed()

    def extend(self, x):
        new_value = []
        for i in x:
            i = self.__item_type__.coerce(None, i)
            i._parents = self._parents
            new_value.append(i)
        list.extend(self, new_value)
        self.changed()

    def insert(self, i, x):
        list.insert(self, i, self.observe_item(x))
        self.changed()

    @classmethod
    def coerce(cls, index, value):

        if not isinstance(value, cls):

            if isinstance(value, Iterable):
                result = cls()

                for i in value:
                    item = cls.__item_type__.coerce(index, i)
                    # item.set_parent(result)
                    result.append(item)
                return result

            return super().coerce(index, value)

        else:
            return value


class Model(Base):
    __tablename__ = 'my_data'
    id = Column(Integer, primary_key=True)
    data = Column(ImageList.as_mutable(JSONEncodedDict))

    def __repr__(self):
        return "<%s data=%s>" % (self.id, self.data)


Base.metadata.create_all(engine, checkfirst=True)


if __name__ == '__main__':
    session = session_factory()

    m = Model()
    m.data = MutableList()
    m.data.append({'name': 'vahid'})
    session.add(m)
    session.commit()
    # m.data[0].update({'last': 'mardani'})
    m.data[0]['key2'] = 'value2'
    # m.data.changed()
    # m.data = [{'last': 'mardani'}]
    session.commit()
    print(m)
    m = session.query(Model).one()
    print(m)
