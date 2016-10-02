
    import json
    import functools
    from os.path import join, exists

    from sqlalchemy import Column, Integer, create_engine, Unicode, TypeDecorator
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_media import Image, StoreManager, FileSystemStore


    TEMP_PATH = '/tmp/sqlalchemy-media'
    Base = declarative_base()
    engine = create_engine('sqlite:///:memory:', echo=False)


    # Sqlite is not supporting JSON type, so emulating it:
    class Json(TypeDecorator):
        impl = Unicode

        def process_bind_param(self, value, engine):
            return json.dumps(value)

        def process_result_value(self, value, engine):
            if value is None:
                return None

            return json.loads(value)


    class Person(Base):
        __tablename__ = 'person'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode(100))
        image = Column(Image.as_mutable(Json))

        def __repr__(self):
            return "<%s id=%s>" % (self.name, self.id)


    Base.metadata.create_all(engine, checkfirst=True)
    session_factory = sessionmaker(bind=engine)
    StoreManager.register('fs', functools.partial(FileSystemStore, TEMP_PATH, 'http://static.example.org/'), default=True)

    if __name__ == '__main__':
        session = session_factory()

        with StoreManager(session):
            person1 = Person()
            person1.image = Image.create_from('https://www.python.org/static/img/python-logo@2x.png')
            session.commit()
            print(person1.image)
            path = join(TEMP_PATH, person1.image.path)
            print(path)
            print(person1.image.locate())
            assert exists(path)
