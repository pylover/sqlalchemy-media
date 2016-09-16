
from sqlalchemy import Column, Integer, create_engine, Unicode, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=False)


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100))

    def __repr__(self):
        return "<%s id=%s>" % (self.name, self.id)


Base.metadata.create_all(engine, checkfirst=True)


session_factory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=True,
    twophase=False)

# standard decorator style
@event.listens_for(session_factory, 'after_attach')
def receive_after_attach(session, instance):
    print(instance)


def main():
    session = session_factory()
    session.add_all([Person(name='person%s' % i) for i in range(10)])
    session.commit()
    print('#' * 10)
    for p in session.query(Person):
        print('wow:', p)



if __name__ == '__main__':
    main()
