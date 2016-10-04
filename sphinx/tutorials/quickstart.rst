Attaching Files
===============

This is how to attach image file to sqlalchemy model using the :class:`.FileSystemStore`.


1. Creating workbench
---------------------

Setting up and ``engine`` along-side the ``session_factory``. And creating a constant for the directory to store files.

..  testcode:: quickstart

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.declarative import declarative_base

        TEMP_PATH = '/tmp/sqlalchemy-media'
        Base = declarative_base()
        engine = create_engine('sqlite:///:memory:', echo=False)
        session_factory = sessionmaker(bind=engine)


2. Storage
----------

Registering a default factory for :class:`.FileSystemStore` class. the :class:`.StoreManager` will call it when needed.

..  testcode:: quickstart

        import functools

        from sqlalchemy_media import StoreManager, FileSystemStore

        StoreManager.register(
            'fs',
            functools.partial(FileSystemStore, TEMP_PATH, 'http://static.example.org/'),
            default=True
        )

3. Backend Type
---------------

We are using the sqlite's memory db in this tutorial, because it's so handy. but it's not supporting the JSON data type,
So, this is how to emulate a type using the
`SqlAlchemy Type Decorators <http://docs.sqlalchemy.org/en/latest/core/custom_types.html#typedecorator-recipes>`_.

..  testcode:: quickstart

        import json

        from sqlalchemy import TypeDecorator, Unicode

        class Json(TypeDecorator):
            impl = Unicode

            def process_bind_param(self, value, engine):
                return json.dumps(value)

            def process_result_value(self, value, engine):
                if value is None:
                    return None

                return json.loads(value)


.. note:: You can use any type to store dictionary and list as described on top, but the postgreSql ``HStore`` and
          ``JSON`` are preferred.


4. Defining The Model
---------------------

As described in
`Sqlalchemy's documentation <http://docs.sqlalchemy.org/en/latest/orm/extensions/mutable.html#sqlalchemy.ext.mutable.Mutable.as_mutable>`_,
the ``as_mutable`` method is used to make a type mutable.

..  testcode:: quickstart

        from sqlalchemy import Column, Integer

        from sqlalchemy_media import Image

        class Person(Base):
            __tablename__ = 'person'

            id = Column(Integer, primary_key=True)
            name = Column(Unicode(100))
            image = Column(Image.as_mutable(Json))

            def __repr__(self):
                return "<%s id=%s>" % (self.name, self.id)

5. DB Schema
------------

Making database objects using the famous function ``create_all``, and creating a session instance to interact with
database.

..  testcode:: quickstart

        Base.metadata.create_all(engine, checkfirst=True)
        session = session_factory()


6. Action !
-----------


..  testcode:: quickstart

        from os.path import join, exists

        with StoreManager(session):
            person1 = Person()
            person1.image = Image.create_from('https://www.python.org/static/img/python-logo@2x.png')
            session.add(person1)
            session.commit()

            print('Content type:', person1.image.content_type)
            print('Extension:', person1.image.extension)
            print('Length:', person1.image.length)
            print('Original filename:', person1.image.original_filename)

..  testoutput:: quickstart

        Content type: image/png
        Extension: .png
        Length: 15770
        Original filename: https://www.python.org/static/img/python-logo@2x.png


Call ``person1.image.locate()`` to get the files URL in store.
