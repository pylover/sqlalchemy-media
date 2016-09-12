from sqlalchemy import Column, Integer, create_engine, Unicode
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.indexable import index_property


Base = declarative_base()
engine = create_engine('postgresql://postgres:postgres@localhost/deleteme_jsonb', echo=True)

#  CREATE INDEX foo ON publishers ((info ->> 'name'))


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100))

    def __repr__(self):
        return "%s %s" % (self.id, self.name)


Base.metadata.create_all(engine, checkfirst=True)


# i = Index('idx_profile_name', Person.profile['name'].astext)
# i.create(engine)

session_factory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=True,
    twophase=False)

call_count = 0


def worker():
    session = session_factory()
    vahid, shahab = (Person(name=n) for n in('vahid', 'shahab'))
    session.add_all([vahid, shahab])
    session.commit()



if __name__ == '__main__':
    worker()
