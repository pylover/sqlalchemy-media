API Reference
=============


attachments Module
------------------

.. module:: sqlalchemy_media.attachments

Attachment
^^^^^^^^^^

.. autoclass:: Attachment

   .. autoattribute:: __directory__
   .. autoattribute:: __prefix__
   .. autoattribute:: __max_length__
   .. autoattribute:: __min_length__
   .. autoattribute:: __pre_processors__


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

BaseImage
^^^^^^^^^

.. autoclass:: BaseImage


Image
^^^^^

.. autoclass:: Image

   .. autoattribute:: __directory__
   .. autoattribute:: __prefix__
   .. autoattribute:: __max_length__
   .. autoattribute:: __min_length__


ImageList
^^^^^^^^^

.. autoclass:: ImageList

   .. autoattribute:: __item_type__


Thumbnail
^^^^^^^^^

.. autoclass:: Thumbnail


descriptors Module
------------------

.. module:: sqlalchemy_media.descriptors

BaseDescriptor
^^^^^^^^^^^^^^

.. autoclass:: BaseDescriptor

   .. automethod:: _tell_source
   .. automethod:: _read_source


StreamDescriptor
^^^^^^^^^^^^^^^^

.. autoclass:: StreamDescriptor

StreamCloserDescriptor
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: StreamCloserDescriptor

LocalFileSystemDescriptor
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: LocalFileSystemDescriptor

UrlDescriptor
^^^^^^^^^^^^^

.. autoclass:: UrlDescriptor

CgiFieldStorageDescriptor
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: CgiFieldStorageDescriptor

AttachableDescriptor
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: AttachableDescriptor

stores Module
-------------

.. module:: sqlalchemy_media.stores

Store
^^^^^

.. autoclass:: Store

FileSystemStore
^^^^^^^^^^^^^^^

.. autoclass:: FileSystemStore

S3Store
^^^^^^^

.. autoclass:: S3Store


OS2Store
^^^^^^^^

.. autoclass:: OS2Store


SSHStore
^^^^^^^^

.. autoclass:: SSHStore


StoreManager
^^^^^^^^^^^^

.. autoclass:: StoreManager

   .. automethod:: __enter__
   .. automethod:: __exit__


processors Module
-----------------

.. module:: sqlalchemy_media.processors

Processor
^^^^^^^^^

.. autoclass:: Processor


Analyzer
^^^^^^^^

.. autoclass:: Analyzer

MagicAnalyzer
^^^^^^^^^^^^^

.. autoclass:: MagicAnalyzer


WandAnalyzer
^^^^^^^^^^^^

.. autoclass:: WandAnalyzer


PILAnalyzer
^^^^^^^^^^^

.. autoclass:: PILAnalyzer


Validator
^^^^^^^^^

.. autoclass:: Validator

ContentTypeValidator
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ContentTypeValidator


ImageValidator
^^^^^^^^^^^^^^

.. autoclass:: ImageValidator


ImageProcessor
^^^^^^^^^^^^^^

.. autoclass:: ImageProcessor


PILImageProcessor
^^^^^^^^^^^^^^^^^

.. autoclass:: PILImageProcessor


exceptions Module
-----------------

.. module:: sqlalchemy_media.exceptions

.. autoexception:: SqlAlchemyMediaException

.. autoexception:: MaximumLengthIsReachedError

.. autoexception:: MinimumLengthIsNotReachedError

.. autoexception:: ContextError

.. autoexception:: DefaultStoreError

.. autoexception:: AnalyzeError

.. autoexception:: ValidationError

.. autoexception:: DescriptorOperationError

.. autoexception:: DescriptorError

.. autoexception:: OptionalPackageRequirementError

.. autoexception:: ContentTypeValidationError

.. autoexception:: ThumbnailIsNotAvailableError

.. autoexception:: DimensionValidationError


Other Modules
-------------

.. automodule:: sqlalchemy_media.mimetypes_

.. automodule:: sqlalchemy_media.optionals

.. automodule:: sqlalchemy_media.constants


