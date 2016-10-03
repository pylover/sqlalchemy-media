from typing import Hashable
import copy
import uuid
import time
from os.path import splitext
from collections import Iterable

from sqlalchemy.ext.mutable import MutableList, MutableDict

from sqlalchemy_media.stores import StoreManager, Store
from sqlalchemy_media.typing_ import Attachable
from sqlalchemy_media.descriptors import AttachableDescriptor
from sqlalchemy_media.constants import MB, KB


class Attachment(MutableDict):
    """
    The base model for an attached file.
    All attachment types will be inherited from this class.

    Actually this is an instance of :class:`sqlalchemy.ext.mutable.MutableDict` which inherited from :class:`dict`.

    .. doctest::

        >>> from sqlalchemy_media import Attachment
        >>> print(Attachment(key1='Value1'))
        {'key1': 'Value1'}


    This object is should be used inside a :class:`.StoreManager` context.

    """

    #: The directory name of the file.
    __directory__ = 'attachments'

    #: The prefix to be prepended an the name of the file.
    __prefix__ = 'attachment'

    #: Limit the file's maximum size.
    __max_length__ = None

    #: Limit the file's minimum size.
    __min_length__ = None

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        StoreManager.observe_attribute(attribute)
        super()._listen_on_attribute(attribute, coerce, parent_cls)

    @classmethod
    def _assert_type(cls, value) -> None:
        """
        Checking attachment type, raising :exc:`TypeError` if the value is not derived from :class:`.Attachment`.

        """
        if isinstance(value, Attachment) and not isinstance(value, cls):
            raise TypeError('Value type must be subclass of %s' % cls)

    @classmethod
    def coerce(cls, key, value) -> 'Attachment':
        """
        Converts plain dictionary to instance of this class.

        .. seealso:: :meth:`sqlalchemy.ext.mutable.MutableDict.coerce`

        """
        cls._assert_type(value)
        return super().coerce(key, value)

    @classmethod
    def create_from(cls, *args, **kwargs):
        """
        Factory method to create and attach file with the same action.

        :param args: The same as the :meth:`.attach`
        :param kwargs: The same as the :meth:`.attach`
        :return: The loaded instance of this class.
        """
        instance = cls()
        instance.attach(*args, **kwargs)
        return instance

    def __hash__(self) -> int:
        """
        Returns the unique hash of this attachment based on :attr:`.key`

        """
        return hash(self.key)

    @property
    def store_id(self) -> str:
        """
        Returns the id of store used to put this file on.

        Stores must be registered with appropriate id via :meth:`.StoreManager.register`.

        :type: str
        """
        return self.get('storeId')

    @store_id.setter
    def store_id(self, value) -> None:
        self['storeId'] = value

    @property
    def key(self) -> Hashable:
        """
        Unique key for tracking this attachment. it will be generated during attachment process in
        :meth:`.attach` method.

        :type: Hashable
        """
        return self.get('key')

    @key.setter
    def key(self, value) -> None:
        self['key'] = value

    @property
    def empty(self) -> bool:
        """
        Check if file is attached to this object or not. Returns :const:`True` when a file is loaded on this object via
        :meth:`.attach` method. or SqlAlchemy db load mechanism. else :const:`False.`

        :type: bool
        """
        return self.key is None

    @property
    def path(self) -> str:
        """
        Relative Path of the file used to store and locate the file.

        :type: str
        """
        return '%s/%s' % (self.__directory__, self.filename)

    @property
    def filename(self) -> str:
        """
        The filename used to store the attachment in storage. with this format:
        '{self.__prefix__}-{self.key}{self.suffix}{if self.extension else ''}'

        :type: str
        """
        return '%s-%s%s%s' % (self.__prefix__, self.key, self.suffix, self.extension if self.extension else '')

    @property
    def suffix(self) -> str:
        """
        The same as the :meth:`sqlalchemy_media.attachments.Attachment.original_filename` plus a leading minus(-)
        If available, else empty string ('') will be returned

        :type: str
        """
        if self.original_filename:
            return '-%s' % splitext(self.original_filename)[0]
        return ''

    @property
    def extension(self) -> str:
        """
        File extension.

        :type: str
        """
        return self.get('extension')

    @extension.setter
    def extension(self, value) -> None:
        self['extension'] = value

    @property
    def content_type(self) -> str:
        """
        file Content-Type

        :type: str
        """
        return self.get('contentType')

    @content_type.setter
    def content_type(self, value) -> None:
        self['contentType'] = value

    @property
    def original_filename(self) -> str:
        """
        Original file name, may provided by user within :attr:`cgi.FieldStorage.filename`, url or Physical filename.

        :type: str
        """
        return self.get('originalFilename')

    @original_filename.setter
    def original_filename(self, value) -> None:
        self['originalFilename'] = value

    @property
    def length(self) -> int:
        """
        The length of the attached file in bytes.

        :type: int
        """
        return int(self.get('length'))

    @length.setter
    def length(self, value) -> None:
        self['length'] = value

    @property
    def timestamp(self):
        """
        The unix-time of the attachment creation.

        :type: str
        """
        return self.get('timestamp')

    @timestamp.setter
    def timestamp(self, v: [str, float]):
        self['timestamp'] = str(v) if not isinstance(v, str) else v

    def copy(self) -> 'Attachment':
        """
        Copy this object using deepcopy
        """
        return self.__class__(copy.deepcopy(self))

    def get_store(self) -> Store:
        """
        Returns the :class:`sqlalchemy_media.stores.Store` instance, which this file is stored on.
        """
        store_manager = StoreManager.get_current_store_manager()
        return store_manager.get(self.store_id)

    def delete(self) -> None:
        """
        Deletes the file.

        .. warning:: This operation is can not be roll-backed.So if you want to delete a file, just set it's to
                     :const:`None`, set it by new :class:`.Attachment` instance.
        """
        self.get_store().delete(self.path)

    def attach(self, attachable: Attachable, content_type: str = None, original_filename: str = None, extension: str = None,
               store_id: str = None, overwrite: bool=False) -> None:
        """
        Attach a file. if the session roll-backed, all operations will be rolled-back.
        The old file will be deleted after commit, if any.

        :param attachable: stream, filename or URL to attach.
        :param content_type: If given, the content-detection is suppressed.
        :param original_filename: Original name of the file, if available, to append on the filename, useful for SEO,
                                  and readability.
        :param extension: The file's extension, is available.else, trying to guess it by content_type
        :param store_id: The store id to store this file on. Stores must be registered with appropriate id via
                         :meth:`sqlalchemy_media.stores.StoreManager.register`.
        :param overwrite: Overwrites the file without changing it's unique-key and name, useful to prevent broken links.
                          Currently, when using this option, Rollback function is not available, because the old file
                          will overwritten by the given new one.

        .. note:: :exc:`.MaximumLengthIsReachedError` and or :exc:`.MinimumLengthIsNotReachedError` may raised.
        """

        # Wrap in AttachableDescriptor
        with AttachableDescriptor(
                attachable,
                content_type=content_type,
                original_filename=original_filename,
                extension=extension
        ) as descriptor:

            # Backup the old key and filename if exists
            if overwrite:
                old_attachment = None
            else:
                old_attachment = None if self.empty else self.copy()
                self.key = str(uuid.uuid4())

            # Analyze
            # Validate
            # Store
            if descriptor.original_filename:
                self.original_filename = descriptor.original_filename

            if descriptor.extension:
                self.extension = descriptor.extension

            if descriptor.content_type:
                self.content_type = descriptor.content_type

            if store_id is not None:
                self.store_id = store_id

            self['length'] = self.get_store().put(
                self.path,
                descriptor,
                max_length=self.__max_length__,
                min_length=self.__min_length__
            )

            self.timestamp = time.time()

            store_manager = StoreManager.get_current_store_manager()
            store_manager.register_to_delete_after_rollback(self)

            if old_attachment:
                store_manager.register_to_delete_after_commit(old_attachment)

    def locate(self) -> str:
        """
        Locates the file url.
        """
        store = self.get_store()
        return '%s?_ts=%s' % (store.locate(self), self.timestamp)


class AttachmentCollection(object):
    """
    Mixin to make a collection of :class:`.Attachment`

    """

    #: Type of items
    __item_type__ = Attachment

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        StoreManager.observe_attribute(attribute, collection=True)
        # noinspection PyUnresolvedReferences
        # noinspection PyProtectedMember
        super()._listen_on_attribute(attribute, coerce, parent_cls)


class AttachmentList(AttachmentCollection, MutableList):
    """
    Used to create a collection of :class:`.Attachment`
    ::

        class MyList(AttachmentList):
            __item_type__ = MyAttachment

        class Person(BaseModel):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            files = Column(MyList.as_mutable(Json))

        me = Person()
        me.files = MyList()
        me.files.append(MyAttachment.create_from(any_file))

    """

    @classmethod
    def coerce(cls, index, value):

        if isinstance(value, Iterable):
            result = cls()
            for i in value:
                result.append(cls.__item_type__.coerce(index, i))
            return result

        return super().coerce(index, value)

    def append(self, x):
        super().append(x)
        StoreManager.get_current_store_manager().adopted(x)

    def remove(self, i):
        super().remove(i)
        StoreManager.get_current_store_manager().orphaned(i)

    def pop(self, *args):
        i = super().pop(*args)
        StoreManager.get_current_store_manager().orphaned(i)
        return i

    def extend(self, x):
        StoreManager.get_current_store_manager().adopted(*x)
        super().extend(x)

    def insert(self, i, x):
        StoreManager.get_current_store_manager().adopted(x)
        super().insert(i, x)

    def clear(self):
        StoreManager.get_current_store_manager().orphaned(*self)
        super().clear()

    def __delitem__(self, index):
        StoreManager.get_current_store_manager().orphaned(self[index])
        super().__delitem__(index)

    def __setitem__(self, index, value):
        old_value = self[index]
        store_manager = StoreManager.get_current_store_manager()
        if old_value:
            store_manager.orphaned(old_value)

        store_manager.adopted(value)
        super().__setitem__(index, value)

    def __setslice__(self, start, end, value):
        store_manager = StoreManager.get_current_store_manager()
        store_manager.orphaned(*[i for i in self[start:end] if i])
        store_manager.adopted(*value)
        super().__setslice__(start, end, value)

    def __delslice__(self, start, end):
        StoreManager.get_current_store_manager().orphaned(*[i for i in self[start:end] if i])
        super().__delslice__(start, end)


class AttachmentDict(AttachmentCollection, MutableDict):
    """
    Used to create a dictionary of :class:`.Attachment`

    ::

        class MyDict(AttachmentDict):
            __item_type__ = MyAttachment

        class Person(BaseModel):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            files = Column(MyDict.as_mutable(Json))

        me = Person()
        me.files = MyDict()
        me.files['original'] = MyAttachment.create_from(any_file)
    """

    @classmethod
    def coerce(cls, index, value):

        if isinstance(value, dict) and not isinstance(value, (AttachmentDict, Attachment)):
            result = cls()
            for k, v in value.items():
                result[k] = cls.__item_type__.coerce(k, v)
            return result

        return super().coerce(index, value)

    def setdefault(self, key, value):
        StoreManager.get_current_store_manager().adopted(value)
        return super().setdefault(key, value)

    def update(self, *a, **kw):
        StoreManager.get_current_store_manager().adopted(kw.values())
        super().update(*a, **kw)

    def pop(self, *args):
        i = super().pop(*args)
        StoreManager.get_current_store_manager().orphaned(i)
        return i

    def popitem(self):
        k, v = super().popitem()
        StoreManager.get_current_store_manager().orphaned(v)
        return k, v

    def clear(self):
        StoreManager.get_current_store_manager().orphaned(*self.values())
        super().clear()

    def __delitem__(self, key):
        StoreManager.get_current_store_manager().orphaned(self[key])
        super().__delitem__(key)

    def __setitem__(self, key, value):
        StoreManager.get_current_store_manager().adopted(value)
        super().__setitem__(key, value)


class File(Attachment):
    """
    Representing an attached file. Normally if you want to store any file, this class is the best choice.
    """

    __directory__ = 'files'
    __prefix__ = 'file'
    __max_length__ = 2 * MB
    __min_length__ = 0


class FileList(AttachmentList):
    """
    Equivalent to
    ::

        class FileList(AttachmentList):
            __item_type__ = File

    """
    __item_type__ = File


class FileDict(AttachmentDict):
    """
    Equivalent to
    ::

        class FileDict(AttachmentDict):
            __item_type__ = File

    """
    __item_type__ = File


class Image(File):
    """
    Equivalent to
    ::

        class Image(Attachment):
            __directory__ = 'images'
            __prefix__ = 'image'
            __max_length__ = 2 * MB
            __min_length__ = 4 * KB

    """

    __directory__ = 'images'
    __prefix__ = 'image'

    __max_length__ = 2 * MB
    __min_length__ = 4 * KB
