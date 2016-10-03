API Reference
=============


attachments
-----------

.. module:: sqlalchemy_media.attachments

Attachment
^^^^^^^^^^

.. autoclass:: Attachment

   .. autoattribute:: __directory__
   .. autoattribute:: __prefix__
   .. autoattribute:: __max_length__
   .. autoattribute:: __min_length__


AttachmentCollection
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: AttachmentCollection

   .. autoattribute:: __item_type__


AttachmentList
^^^^^^^^^^^^^^

.. autoclass:: AttachmentList

AttachmentDict
^^^^^^^^^^^^^^

.. autoclass:: AttachmentDict

File
^^^^

.. autoclass:: File

   .. autoattribute:: __directory__
   .. autoattribute:: __prefix__
   .. autoattribute:: __max_length__
   .. autoattribute:: __min_length__

FileList
^^^^^^^^

.. autoclass:: FileList

   .. autoattribute:: __item_type__

FileDict
^^^^^^^^

.. autoclass:: FileDict

   .. autoattribute:: __item_type__

Image
^^^^^

.. autoclass:: Image

   .. autoattribute:: __directory__
   .. autoattribute:: __prefix__
   .. autoattribute:: __max_length__
   .. autoattribute:: __min_length__

stores
------

.. module:: sqlalchemy_media.stores

Store
^^^^^

.. autoclass:: Store

FileSystemStore
^^^^^^^^^^^^^^^

.. autoclass:: FileSystemStore

StoreManager
^^^^^^^^^^^^

.. autoclass:: StoreManager

exceptions
----------

.. module:: sqlalchemy_media.exceptions

.. autoexception:: SqlAlchemyMediaException

.. autoexception:: MaximumLengthIsReachedError

.. autoexception:: MinimumLengthIsNotReachedError

.. autoexception:: ContextError

.. autoexception:: DefaultStoreError

constants
---------

.. automodule:: sqlalchemy_media.constants


