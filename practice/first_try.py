import unittest

from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB


class Media(TypeDecorator):
    impl = JSONB

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value

    def copy(self, **kw):
        return Media(**kw)


class MediaTypeTestCase(unittest.TestCase):
    def test_crud(self):
        from sqlalchemy import Column, Integer, create_engine, Index, MetaData, Table
        from sqlalchemy.

        class Person()


if __name__ == '__main__':
    unittest.main()
