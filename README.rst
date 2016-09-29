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

.. image:: https://img.shields.io/badge/license-GPLv3-brightgreen.svg
     :target: https://github.com/pylover/sqlalchemy-media/blob/master/LICENSE



Attaching any files(Image, Video & etc ) into sqlalchemy models using configurable stores including FileSystemStore.


Overview
--------

 - Store and locate any file.
 - Using json backend type. but supporting all dialects using VARCHAR as json string.
 - Using SqlAlchemy mutables, it's so fun!
 - Offering delete_orphan flag, to automatically delete files which orphaned via attribute set or delete from 
    collections.
