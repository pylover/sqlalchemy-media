from sqlalchemy import Column, Integer, create_engine, Index, Text
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
    profile = Column(JSONB(none_as_null=True, astext_type=Text))
    name = index_property('profile', 'name', datatype=dict)

    # __table_args__ = (, )

    def __repr__(self):
        return "%s %s %s" % (self.id, self.name, self.profile)


Base.metadata.create_all(engine, checkfirst=True)

from sqlalchemy import inspect
insp = inspect(engine)
for idx in insp.get_indexes('person'):
    if idx['name'] == 'idx_person_profile_name':
       break
    else:
        engine.execute("CREATE INDEX idx_person_profile_name ON person ((profile ->> 'name'))")





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

    vahid.profile.update({
        'age': 35,
        'job': 'Senior Developer',
        'days': [1, 4, 5, 6, 8],
        'skills': {
            'sysadmin': 100,
            'programming': 100,
            'speaking': 80
        }
    })

    shahab.profile.update({
        'age': 28,
        'job': 'Senior Developer',
        'days': [1, 4, 5, 67, 8],
        'skills': {
            'sysadmin': 100,
            'programming': 100,
            'speaking': 70
        }
    })

    session.add_all([vahid, shahab])
    session.commit()

    for p in session.query(Person)\
            .filter(Person.name.astext == 'vahid')\
            .filter(Person.profile.contains({"age": 35, "skills": {"speaking": 80}})):
        print(p)
        # print(p.name, p.profile)


if __name__ == '__main__':
    worker()
