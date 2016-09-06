
from sqlalchemy import Column, Integer, create_engine, Index, MetaData, Table
from sqlalchemy.dialects.postgresql import JSONB

e = create_engine("postgresql://postgres:postgres@localhost/deleteme_jsonb", echo=True)

m = MetaData()
publishers = Table('publishers', m, Column('id', Integer), Column('info', JSONB))

Index("foo", publishers.c.info['name'].astext)

m.create_all(e)
