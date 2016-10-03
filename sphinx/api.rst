API Reference
=============


attachments
-----------

.. currentmodule:: sqlalchemy_media.attachments

Attachment
^^^^^^^^^^

.. autoclass:: Attachment
    :members: __directory__, __prefix__, __max_length__, __min_length__
    :show-inheritance:

AttachmentCollection
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: AttachmentCollection
    :members:
    :show-inheritance:

AttachmentList
^^^^^^^^^^^^^^

.. autoclass:: AttachmentList
    :members:
    :show-inheritance:


AttachmentDict
^^^^^^^^^^^^^^

.. autoclass:: AttachmentDict
    :members:
    :show-inheritance:

FileList
^^^^^^^^

.. autoclass:: FileList
    :members:
    :show-inheritance:

FileDict
^^^^^^^^

.. autoclass:: FileDict
    :members:
    :show-inheritance:

Image
^^^^^

.. autoclass:: Image
    :members:
    :show-inheritance:


stores
------

.. currentmodule:: sqlalchemy_media.stores

Store
^^^^^

.. autoclass:: Store
    :members:
    :show-inheritance:

FileSystemStore
^^^^^^^^^^^^^^^

.. autoclass:: FileSystemStore
    :members:
    :show-inheritance:

StoreManager
^^^^^^^^^^^^

.. autoclass:: StoreManager
    :members:
    :show-inheritance:


exceptions
----------

.. currentmodule:: sqlalchemy_media.exceptions


.. autoexception:: SqlAlchemyMediaException
   :show-inheritance:
   :members:
   :undoc-members:

.. autoexception:: MaximumLengthIsReachedError
   :show-inheritance:
   :members:
   :undoc-members:

.. autoexception:: MinimumLengthIsNotReachedError
   :show-inheritance:
   :members:
   :undoc-members:
