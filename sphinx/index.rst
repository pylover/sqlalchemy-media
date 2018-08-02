
.. sqlalchemy-media documentation master file, created by
   sphinx-quickstart on Mon Jul 20 22:05:40 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. DOC TODO:
   - Document about customizing the attachment by inheriting


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

.. image:: https://img.shields.io/github/stars/pylover/sqlalchemy-media.svg?style=social&label=Star
     :target: https://github.com/pylover/sqlalchemy-media

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
 - Auto generating thumbnails, using ``width``, ``height`` and or ``ratio``.
 - Analyzing files & images using ``magic`` and ``wand``.
 - Validating ``mimetype``, ``width``, ``height`` and image ``ratio``.
 - Automatically resize & reformat images before store.


Contents:
---------


.. toctree::
   :maxdepth: 4

   install
   tutorials/index
   api



Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

