sqlalchemy-media
================


.. image:: http://img.shields.io/pypi/v/sqlalchemy-media.svg
     :target: https://pypi.python.org/pypi/sqlalchemy-media

.. image:: https://requires.io/github/pylover/sqlalchemy-media/requirements.svg?branch=master
     :target: https://requires.io/github/pylover/sqlalchemy-media/requirements/?branch=master
     :alt: Requirements Status

.. image:: https://travis-ci.org/pylover/sqlalchemy-media.svg?branch=master
     :target: https://travis-ci.org/pylover/sqlalchemy-media

.. image:: https://coveralls.io/repos/github/pylover/sqlalchemy-media/badge.svg?branch=master
     :target: https://coveralls.io/github/pylover/sqlalchemy-media?branch=master

.. image:: https://img.shields.io/badge/license-MIT-brightgreen.svg
     :target: https://github.com/pylover/sqlalchemy-media/blob/master/LICENSE


Documentation
-------------

See the `documentation <http://sqlalchemy-media.dobisel.com>`_ for full description.


Why ?
-----
Nowadays, most of the database applications are used to allow users to upload and attach files of various types to
ORM models.

Handling those jobs is not simple if you have to care about Security, High-Availability, Scalability, CDN and more
things you may have already been concerned. Accepting a file from public space, analysing, validating,
processing(Normalizing) and making it available to public space again is the main goal of this project.

Sql-Alchemy is the best platform for implementing this stuff. It has the
`SqlAlchemy Mutable <http://docs.sqlalchemy.org/en/latest/orm/extensions/mutable.html>`_ types facility to manipulate
the objects with any type in-place. why not ?

.. note:: The main idea comes from `dahlia's SQLAlchemy-ImageAttach <https://github.com/dahlia/sqlalchemy-imageattach>`_.

Overview
--------

 - Storing and locating any file, tracking it by sqlalchemy models.
 - Storage layer is completely separated from data model, with a simple api: (put, delete, open, locate)
 - Using any SqlAlchemy data type which interfaces Python dictionary. This is achieved by using the
   `SqlAlchemy Type Decorators <http://docs.sqlalchemy.org/en/latest/core/custom_types.html#typedecorator-recipes>`_ and
   `SqlAlchemy Mutable <http://docs.sqlalchemy.org/en/latest/orm/extensions/mutable.html>`_.
 - Offering ``delete_orphan`` flag to automatically delete files which orphaned via attribute set or delete from
   collections, or objects leaved in memory alone! by setting it's last pointer to None.
 - Attaching files from Url, LocalFileSystem and Streams.
 - Extracting the file's mimetype from the backend stream if possible, using ``magic`` module.
 - Limiting file size(min, max), to prevent DOS attacks.
 - Adding timestamp in url to help caching.
 - Using python type hinting to annotate arguments. So currently python3.5 and higher is supported.
 - Auto generating thumbnails, using ``width``, ``height`` and or ``ratio``.
 - Analyzing files & images using ``magic`` and ``wand``.
 - Validating ``mimetype``, ``width``, ``height`` and image ``ratio``.
 - Automatically resize & reformat images before store.

Quick Start
-----------

Here is a simple example to see how to use this library:

.. code-block:: python

  import functools
  import json
  from os.path import exists, join

  from sqlalchemy import create_engine, TypeDecorator, Unicode, Column, Integer
  from sqlalchemy.orm import sessionmaker
  from sqlalchemy.ext.declarative import declarative_base

  from sqlalchemy_media import StoreManager, FileSystemStore, Image, WandAnalyzer, ImageValidator, ImageProcessor


  TEMP_PATH = '/tmp/sqlalchemy-media'
  Base = declarative_base()
  engine = create_engine('sqlite:///:memory:', echo=False)
  session_factory = sessionmaker(bind=engine)


  StoreManager.register(
      'fs',
      functools.partial(FileSystemStore, TEMP_PATH, 'http://static.example.org/'),
      default=True
  )


  class Json(TypeDecorator):
      impl = Unicode

      def process_bind_param(self, value, engine):
          return json.dumps(value)

      def process_result_value(self, value, engine):
          if value is None:
              return None

          return json.loads(value)


  class ProfileImage(Image):
      __pre_processors__ = [
          WandAnalyzer(),
          ImageValidator(
              minimum=(80, 80),
              maximum=(800, 600),
              min_aspect_ratio=1.2,
              content_types=['image/jpeg', 'image/png']
          ),
          ImageProcessor(
              fmt='jpeg',
              width=120,
              crop=dict(
                  left='10%',
                  top='10%',
                  width='80%',
                  height='80%',
              )
          )
      ]


  class Person(Base):
      __tablename__ = 'person'

      id = Column(Integer, primary_key=True)
      name = Column(Unicode(100))
      image = Column(ProfileImage.as_mutable(Json))

      def __repr__(self):
          return "<%s id=%s>" % (self.name, self.id)


  Base.metadata.create_all(engine, checkfirst=True)

  if __name__ == '__main__':
      session = session_factory()

      with StoreManager(session):
          person1 = Person()
          person1.image = ProfileImage.create_from('https://www.python.org/static/img/python-logo@2x.png')
          session.add(person1)
          session.commit()

          print('Content type:', person1.image.content_type)
          print('Extension:', person1.image.extension)
          print('Length:', person1.image.length)
          print('Original filename:', person1.image.original_filename)

          thumbnail = person1.image.get_thumbnail(width=32, auto_generate=True)
          print(thumbnail.height)
          assert exists(join(TEMP_PATH, thumbnail.path))

          thumbnail = person1.image.get_thumbnail(ratio=.3, auto_generate=True)
          print(thumbnail.width, thumbnail.height)
          assert exists(join(TEMP_PATH, thumbnail.path))

          person1.image.attach('https://www.python.org/static/img/python-logo.png')
          session.commit()

          print('Content type:', person1.image.content_type)
          print('Extension:', person1.image.extension)
          print('Length:', person1.image.length)
          print('Original filename:', person1.image.original_filename)

      with StoreManager(session, delete_orphan=True):
          deleted_filename = join(TEMP_PATH, person1.image.path)
          person1.image = None
          session.commit()

          assert not exists(deleted_filename)

          person1.image = ProfileImage.create_from('https://www.python.org/static/img/python-logo.png')
          session.commit()

          print('Content type:', person1.image.content_type)
          print('Extension:', person1.image.extension)
          print('Length:', person1.image.length)
          print('Original filename:', person1.image.original_filename)


Will produce::

    Content type: image/jpeg
    Extension: .jpg
    Length: 2020
    Original filename: https://www.python.org/static/img/python-logo@2x.png
    8
    28 7
    Content type: image/jpeg
    Extension: .jpg
    Length: 2080
    Original filename: https://www.python.org/static/img/python-logo.png
    Content type: image/jpeg
    Extension: .jpg
    Length: 2080
    Original filename: https://www.python.org/static/img/python-logo.png


Changelog
---------

Here you can see the full list of changes made on each sqlalchemy-media release.

0.6.2
  - Fixing a bug in ``optionals`` module.

0.6.1
  - Fixing some problems in documents.

0.6.0
  - Image crop feature: #16.

0.5.0
  - #17, #55. Merge analizers, validators and processors as processors. for simplicity.

0.4.1 (2016-10-06)
  - #54 Fixed.

0.4.0 (2016-10-05)
  - ImageDimensionValidator: #14
  - WandAnalyzer: #52

0.3.0 (2016-10-05)
  - Thumbnail auto generation implemented: #11,  See doc.
  - Not using python's built-in mimetype module, due the bug: https://bugs.python.org/issue4963

0.2.0 (2016-10-05)
  - Added two tutorials in documentation
  - Restricting Content-type: #28
  - MagicAnalyzer
  - Including all requirements*.txt in distribution: #49
  - Including test stuff in distribution: #36
  - Descriptive error message when an optional package is missing: #48
  - Analyser: #30
  - Validation: #31
  - Fixed two bugs: #42, #41

0.1.1 (2016-10-03)
  - Improving coverage
