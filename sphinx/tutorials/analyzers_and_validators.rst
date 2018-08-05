

Playing with Analyzers and Validators
=====================================

The following tutorial is going to describe how to use restrictions on attached filed:

0. Prerequisites
----------------

Mimetype detection from file's content required the ``magic`` package to be installed.
This is an optional package.

.. code-block:: console

   $ pip install python-magic

1. CV
-----

For the first, let to create a type called ``CV``

..  testcode:: content_type

    from sqlalchemy_media import File, MagicAnalyzer, ContentTypeValidator
    from sqlalchemy_media.constants import MB, KB

    class CV(File):
        __pre_processors__ = [
            MagicAnalyzer(),
            ContentTypeValidator(['application/pdf', 'image/jpeg'])
        ]
        __max_length__ = 6*MB
        __min_length__ = 10*KB


2. Creating workbench
---------------------

..  testcode:: content_type

    import functools

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_media import StoreManager, FileSystemStore

    TEMP_PATH = '/tmp/sqlalchemy-media'
    Base = declarative_base()
    engine = create_engine('sqlite:///:memory:', echo=False)
    session_factory = sessionmaker(bind=engine)

    StoreManager.register(
        'fs',
        functools.partial(FileSystemStore, TEMP_PATH, 'http://static.example.org/'),
        default=True
    )

3. Model
--------

..  testcode:: content_type

    import json

    from sqlalchemy import TypeDecorator, Unicode, Column, Integer

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
        cv = Column(CV.as_mutable(Json))


    Base.metadata.create_all(engine, checkfirst=True)
    session = session_factory()


4. Submitting files
-------------------

..  testcode:: content_type

    import io

    from sqlalchemy_media.exceptions import ContentTypeValidationError

    person1 = Person(cv=CV())
    with StoreManager(session):
        person1.cv.attach('../sqlalchemy_media/tests/stuff/cat.jpg')  # OK

        try:
            person1.cv.attach(io.BytesIO(b'Plain text'))
        except ContentTypeValidationError:
            print("ContentTypeValidationError is raised. It's so bad!")

..  testoutput:: content_type

    ContentTypeValidationError is raised. It's so bad!


..  seealso:: :class:`.ImageAnalizer`, :class:`.ImageValidator` amd :class:`.ImageProcessor`

