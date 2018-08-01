from typing import Hashable, Tuple, List, Iterable
import copy
import uuid
import time
import re
import io
from os.path import splitext

from sqlalchemy.ext.mutable import MutableList, MutableDict

from sqlalchemy_media.stores import StoreManager, Store
from sqlalchemy_media.typing_ import Attachable, Dimension
from sqlalchemy_media.descriptors import AttachableDescriptor
from sqlalchemy_media.constants import MB, KB
from sqlalchemy_media.optionals import ensure_wand
from sqlalchemy_media.helpers import validate_width_height_ratio
from sqlalchemy_media.exceptions import ThumbnailIsNotAvailableError
from sqlalchemy_media.imaginglibs import get_image_factory


class Attachment(MutableDict):
    """
    The base model for an attached file.
    All attachment types will be inherited from this class.

    Actually this is an instance of :class:`sqlalchemy.ext.mutable.MutableDict` which inherited from :class:`dict`.

    ..  doctest::

        >>> from sqlalchemy_media import Attachment
        >>> print(Attachment(key1='Value1'))
        {'key1': 'Value1'}


    This object should be used inside a :class:`.StoreManager` context.

    .. versionchanged:: 0.5

       - removed ``__analyzer__`` attribute, using ``__pre_processors__`` instead.
       - removed ``__validate__`` attribute, using ``__pre_processors__`` instead.

    .. versionadded:: 0.9.6

       - ``reproducible``

    """

    #: The directory name of the file.
    __directory__ = 'attachments'

    #: The prefix to be prepended an the name of the file.
    __prefix__ = 'attachment'

    #: Limit the file's maximum size.
    __max_length__ = None

    #: Limit the file's minimum size.
    __min_length__ = None

    #: An instance of :class:`.Processor`, to convert, reformat & change contents before storing the attachment.
    __pre_processors__ = None

    #: Automatically coerce `:obj:.Attachable` objects. So if True, you can set the models attribute by a `file` or
    # `filename` or :class:`cgi.FieldStorage`.
    __auto_coercion__ = False

    #: The reproducible of the file.
    __reproducible__ = False

    #: It allows to customize the Descriptor.
    __descriptor__ = AttachableDescriptor

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        StoreManager.observe_attribute(attribute)
        super()._listen_on_attribute(attribute, coerce, parent_cls)

    @classmethod
    def coerce(cls, key, value) -> 'Attachment':
        """
        Converts plain dictionary to instance of this class.

        .. seealso:: :meth:`sqlalchemy.ext.mutable.MutableDict.coerce`

        """
        if value is None or isinstance(value, (cls, dict)):
            return super().coerce(key, value)

        if cls.__auto_coercion__:
            if not isinstance(value, (tuple, list)):
                value = (value, )

            return cls.create_from(*value)

        raise TypeError(
            'Value type must be subclass of %s or a tuple(file, mime, [filename]),'
            'but it\'s: %s' % (cls, type(value))
        )

    @classmethod
    def create_from(cls, *args, **kwargs):
        """
        Factory method to create and attach file with the same action.

        :param args: The same as the :meth:`.attach`
        :param kwargs: The same as the :meth:`.attach`
        :return: The loaded instance of this class.
        """
        instance = cls()
        return instance.attach(*args, **kwargs)

    def __hash__(self) -> int:
        """
        Returns the unique hash of this attachment based on :attr:`.key`

        """
        return hash(self.key)

    @property
    def store_id(self) -> str:
        """
        Returns the id of the store used to put this file on.

        Stores must be registered with appropriate id via :meth:`.StoreManager.register`.

        :type: str
        """
        return self.get('store_id')

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
        :meth:`.attach` method or SqlAlchemy db load mechanism, else :const:`False.`

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
        The filename used to store the attachment in the storage with this format::

            '{self.__prefix__}-{self.key}{self.suffix}{if self.extension else ''}'

        :type: str
        """
        return '%s-%s%s%s' % (self.__prefix__, self.key, self.suffix, self.extension if self.extension else '')

    @property
    def suffix(self) -> str:
        """
        The same as the :meth:`sqlalchemy_media.attachments.Attachment.original_filename` plus a leading minus(-)
        If available, else empty string ('') will be returned.

        :type: str
        """
        if self.original_filename:
            return '-%s' % re.sub('[/:.?]+', '_', re.sub('\w+://', '', splitext(self.original_filename)[0]))

        return ''

    @property
    def extension(self) -> str:
        """
        File extension.

        :type: str
        """
        return self.get('extension')

    @property
    def content_type(self) -> str:
        """
        file Content-Type

        :type: str
        """
        return self.get('content_type')

    @property
    def original_filename(self) -> str:
        """
        Original file name, it may be provided by user within :attr:`cgi.FieldStorage.filename`, url or Physical
        filename.

        :type: str
        """
        return self.get('original_filename')

    @property
    def length(self) -> int:
        """
        The length of the attached file in bytes.

        :type: int
        """
        return int(self.get('length'))

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

    @property
    def reproducible(self) -> bool:
        """
        The reproducible of the file.

        :type: bool
        """
        return self.get('reproducible', False)

    def copy(self) -> 'Attachment':
        """
        Copy this object using deepcopy.

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

        .. warning:: This operation can not be roll-backed.So if you want to delete a file, just set it to
                     :const:`None` or set it by new :class:`.Attachment` instance, while passed ``delete_orphan=True``
                     in :class:`.StoreManager`.

        """
        self.get_store().delete(self.path)

    def attach(self, attachable: Attachable, content_type: str = None, original_filename: str = None,
               extension: str = None, store_id: str = None, overwrite: bool=False, suppress_pre_process: bool=False,
               suppress_validation: bool=False, **kwargs) -> 'Attachment':
        """
        Attach a file. if the session is rolled-back, all operations will be rolled-back.
        The old file will be deleted after commit, if any.

        Workflow::


                             +--------+
                             | Start  |
                             +---+----+
                                 |
                      +----------v-----------+
                      | Wrap with Descriptor <----+
                      +----------+-----------+    |
                                 |                |
                      +----------v-----------+    |
                      | Nothing or Analyze   |    |
                      +----------+-----------+    |
                                 |                |
                      +----------v-----------+    |
                      | Nothing or Validate  |    |
                      +----------+-----------+    |
                                 |                |
                      +----------v-----------+    |
                      |Nothing or Pre Process+----+
                      +------+---------------+
                             |
                  +----------+-----------+
                  |                      |
           +------v---------+  +---------v------+
           |  Store in DB   |  |Store In Storage|
           +------+---------+  +---------+------+
                  |                      |
                  +----------+-----------+
                             |
                             |
                         +---v----+
                         | Finish |
                         +--------+


        :param attachable: file-like object, filename or URL to attach.
        :param content_type: If given, the content-detection is suppressed.
        :param original_filename: Original name of the file, if available, to append to the end of the the filename,
                                  useful for SEO, and readability.
        :param extension: The file's extension, is available.else, tries to guess it by content_type
        :param store_id: The store id to store this file on. Stores must be registered with appropriate id via
                         :meth:`sqlalchemy_media.stores.StoreManager.register`.
        :param overwrite: Overwrites the file without changing it's unique-key and name, useful to prevent broken links.
                          Currently, when using this option, Rollback function is not available, because the old file
                          will be overwritten by the given new one.
        :param suppress_pre_process: When is :data:`.True`, ignores the pre-processing phase, during attachment.
        :param suppress_validation: When is :data:`.True`, ignores the validation phase, during attachment.
        :param kwargs: Additional metadata to be stored in backend.

        .. note:: :exc:`.MaximumLengthIsReachedError` and or :exc:`.MinimumLengthIsNotReachedError` may be raised.

        .. warning:: This operation can not be rolled-back, if ``overwrite=True`` given.

        .. versionchanged:: 0.1

            - This method will return the self. it's useful to chain method calls on the object within a single line.
            - Additional ``kwargs`` are accepted to be stored in database alongside the file's metadata.

        .. versionchanged:: 0.5

            - ``suppress_pre_process`` argument.
            - ``suppress_validation`` argument.
            - pre-processing phase.

        """

        # Wrap in AttachableDescriptor
        descriptor = self.__descriptor__(
            attachable,
            content_type=content_type,
            original_filename=original_filename,
            extension=extension,
            max_length=self.__max_length__,
            min_length=self.__min_length__,
            reproducible=self.__reproducible__
        )

        try:

            # Backup the old key and filename if exists
            if overwrite:
                old_attachment = None
            else:
                old_attachment = None if self.empty else self.copy()
                self.key = str(uuid.uuid4())

            # Store information from descriptor
            attachment_info = kwargs.copy()
            attachment_info.update(
                original_filename=descriptor.original_filename,
                extension=descriptor.extension,
                content_type=descriptor.content_type,
                length=descriptor.content_length,
                store_id=store_id,
                reproducible=descriptor.reproducible
            )

            # Pre-processing
            if self.__pre_processors__:
                processors = self.__pre_processors__ if isinstance(self.__pre_processors__, Iterable) \
                    else [self.__pre_processors__]

                # noinspection PyTypeChecker
                for processor in processors:
                    processor.process(descriptor, attachment_info)

            # Updating the mutable dictionary
            self.update([(k, v) for k, v in attachment_info.items() if v is not None])

            # Putting the file on the store.
            self['length'] = self.get_store().put(self.path, descriptor)

            self.timestamp = time.time()

            store_manager = StoreManager.get_current_store_manager()
            store_manager.register_to_delete_after_rollback(self)

            if old_attachment:
                store_manager.register_to_delete_after_commit(old_attachment)
                self.pop('thumbnails', None)

        except:
            descriptor.close(check_length=False)
            raise

        else:
            descriptor.close()

        return self

    def locate(self) -> str:
        """
        Locates the file url.
        """
        store = self.get_store()
        return '%s?_ts=%s' % (store.locate(self), self.timestamp)

    def get_objects_to_delete(self):
        """
        Returns the files to be deleted, if the attachment is marked for deletion.

        """
        yield self

    def get_orphaned_objects(self):
        """
        this method will be always called by the store when adding the ``self`` to the orphaned list. so subclasses
        of the :class:`.Attachment` has a chance to add other related objects into the orphaned list and schedule it
        for delete. for example the :class:`.Image` class can schedule it's thumbnails for deletion also.
        :return: An iterable of :class:`.Attachment` to mark as orphan.

        .. versionadded:: 0.11.0

        """
        return iter([])


class AttachmentCollection(object):
    """
    Mixin to make a mutable iterator as a collection of :class:`.Attachment`.

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

    def observe_item(self, item):
        """
        A simple monkeypatch to instruct the children to notify the parent if contents are changed:

        From `sqlalchemy mutable documentation:
        <http://docs.sqlalchemy.org/en/latest/orm/extensions/mutable.html#sqlalchemy.ext.mutable.MutableList>`_

            Note that MutableList does not apply mutable tracking to the values themselves inside the list. Therefore
            it is not a sufficient solution for the use case of tracking deep changes to a recursive mutable structure,
            such as a JSON structure. To support this use case, build a subclass of MutableList that provides
            appropriate coercion to the values placed in the dictionary so that they too are “mutable”, and emit events
            up to their parent structure.

        :param item: The item to observe
        :return:
        """
        item = self.__item_type__.coerce(None, item)
        item._parents = self._parents
        return item

    @classmethod
    def coerce(cls, index, value):
        if not isinstance(value, cls):
            if isinstance(value, Iterable):
                result = cls()

                # noinspection PyTypeChecker
                for i in value:
                    result.append(cls.__item_type__.coerce(index, i))
                return result
            return super().coerce(index, value)
        else:
            return value

    def append(self, x):
        super().append(self.observe_item(x))
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
        super().extend([self.observe_item(i) for i in x])

    def insert(self, i, x):
        StoreManager.get_current_store_manager().adopted(x)
        super().insert(i, self.observe_item(x))

    def clear(self):
        StoreManager.get_current_store_manager().orphaned(*self)
        super().clear()

    def __delitem__(self, index):
        StoreManager.get_current_store_manager().orphaned(self[index])
        super().__delitem__(index)

    def __setitem__(self, index, value):
        store_manager = StoreManager.get_current_store_manager()
        if isinstance(index, slice):
            for old_value in self[index]:
                if old_value:
                    store_manager.orphaned(old_value)

            for new_item in value:
                store_manager.adopted(new_item)
            super().__setitem__(index, [self.observe_item(i) for i in value])
        else:
            old_value = self[index]
            if old_value:
                store_manager.orphaned(old_value)

            value = self.observe_item(value)
            store_manager.adopted(value)
            super().__setitem__(index, value)


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

        if not isinstance(value, cls):

            if isinstance(value, dict) and not isinstance(value, Attachment):
                result = cls()
                for k, v in value.items():
                    result[k] = cls.__item_type__.coerce(k, v)
                return result

            return super().coerce(index, value)

        else:
            return value

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


class BaseImage(File):
    """
    Base class for all images.

    """

    def attach(self, *args, dimension: Dimension=None, **kwargs):
        """
        A new overload for :meth:`.Attachment.attach`, which accepts one additional argument: ``dimension``.

        :param args: The same as the: :meth:`.Attachment.attach`.
        :param dimension: Image (width, height).
        :param kwargs: The same as the: :meth:`.Attachment.attach`.

        :return: The same as the: :meth:`.Attachment.attach`.

        """
        if dimension:
            kwargs['width'], kwargs['height'] = dimension

        return super().attach(*args, **kwargs)

    @property
    def width(self):
        return self.get('width')

    @property
    def height(self):
        return self.get('height')


class Thumbnail(BaseImage):
    """
    Representing an image thumbnail.

    You may use :meth:`.generate_thumbnail` and or :meth:`.get_thumbnail` with ``auto_generate=True`` to get one.

    """

    __directory__ = 'thumbnails'
    __prefix__ = 'thumbnail'


class Image(BaseImage):
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

    #: It allows to customize the type of thumbnail images.
    __thumbnail_type__ = Thumbnail

    @property
    def thumbnails(self) -> List[Tuple[int, int, float, Thumbnail]]:
        """
        A ``List[Tuple[int, int, float, Thumbnail]]``, to hold thumbnails.

        You may use :meth:`.generate_thumbnail` and or :meth:`.get_thumbnail` with ``auto_generate=True`` to fill it.

        """
        return self.get('thumbnails')

    def generate_thumbnail(self, width: int=None, height: int=None, ratio: float=None, ratio_precision: int=5) \
            -> Thumbnail:
        """

        .. versionadded:: 0.3

        Generates and stores a thumbnail with the given arguments.

        .. warning:: If none or more than one of the ``width``, ``height`` and or ``ratio`` are given, :exc:`ValueError`
                     will be raised.

        :param width: The width of the thumbnail.
        :param height: The Height of the thumbnail.
        :param ratio: The coefficient to reduce, Must be less than ``1.0``.
        :param ratio_precision: Number of digits after the decimal point of the ``ratio`` argument to tune thumbnail
                                lookup precision. default: 2.
        :return: the Newly generated :class:`.Thumbnail` instance.

        """

        # Validating parameters
        width, height, ratio = validate_width_height_ratio(width, height, ratio)

        CompatibleImage = get_image_factory()
        # opening the original file
        thumbnail_buffer = io.BytesIO()
        store = self.get_store()
        with store.open(self.path) as original_file:

            # generating thumbnail and storing in buffer
            # noinspection PyTypeChecker
            img = CompatibleImage(file=original_file)
            img.format = 'jpg'

            with img:
                original_size = img.size

                if callable(width):
                    width = width(original_size)
                if callable(height):
                    height = height(original_size)

                width = int(width)
                height = int(height)

                img.resize(width, height)
                img.save(file=thumbnail_buffer)

        thumbnail_buffer.seek(0)
        if self.thumbnails is None:
            self['thumbnails'] = []

        ratio = round(width / original_size[0], ratio_precision)
        thumbnail = self.__thumbnail_type__.create_from(
            thumbnail_buffer,
            content_type='image/jpeg',
            extension='.jpg',
            dimension=(width, height)
        )
        self.thumbnails.append((width, height, ratio, thumbnail))

        return thumbnail

    def get_thumbnail(self, width: int=None, height: int=None, ratio: float=None, ratio_precision: int=2,
                      auto_generate: bool=False) -> Thumbnail:
        """

        .. versionadded:: 0.3

        Search for the thumbnail with given arguments, if ``auto_generate`` is :data:`.False`, the
        :exc:`.ThumbnailIsNotAvailableError` will be raised, else tries to call the :meth:`generate_thumbnail` to create
        a new one.

        :param width: Width of the thumbnail to search for.
        :param height: Height of the thumbnail to search for.
        :param ratio: Ratio of the thumbnail to search for.
        :param ratio_precision: Number of digits after the decimal point of the ``ratio`` argument to tune thumbnail
                                lookup precision. default: 2.
        :param auto_generate: If :data:`.True`, tries to generate a new thumbnail.

        :return: :class:`.Thumbnail` instance.

        .. warning:: if ``auto_generate`` is :data:`.True`, you have to commit the session, to store the generated
                     thumbnails.

        """

        if ratio:
            ratio = round(ratio, ratio_precision)

        if self.thumbnails is not None:
            for w, h, r, t in self.thumbnails:
                if w == width or h == height or round(r, ratio_precision) == ratio:
                    return self.__thumbnail_type__(t)

        # thumbnail not found
        if auto_generate:
            return self.generate_thumbnail(width, height, ratio)
        else:
            raise ThumbnailIsNotAvailableError(
                'Thumbnail is not available with these criteria: width=%s height=%s ratio=%s' % (width, height, ratio)
            )

    def get_objects_to_delete(self):
        """
        Returns the files to be deleted, if the attachment is marked for deletion.

        """
        yield from super().get_objects_to_delete()
        if self.thumbnails:
            for t in self.thumbnails:
                yield self.__thumbnail_type__(**t[3])

    def get_orphaned_objects(self):
        """
        Mark thumbnails for deletion when the :class:`.Image` is being deleted.
        :return: An iterable of :class:`.Thumbnail` to mark as orphan.

        .. versionadded:: 0.11.0

        """
        if not self.thumbnails:
            return

        for width, height, ratio, thumbnail in self.thumbnails:
            yield self.__thumbnail_type__(thumbnail)


class ImageList(AttachmentList):
    """
    Used to create a collection of :class:`.Image`es

    .. versionadded:: 0.11.0
    """

    __item_type__ = Image
