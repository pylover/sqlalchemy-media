sqlalchemy-media
================

Attaching any files(Image, Video & etc ) into sqlalchemy models using configurable stores including FileSystemStore.


Overview
--------

 - Store and locate any file.
 - Using json backend type. but supporting all dialects using VARCHAR as json string.
 - Using SqlAlchemy mutables, it's so fun!
 - Offering delete_orphan flag, to automatically delete files which orphaned via attribute set or delete from 
    collections.
