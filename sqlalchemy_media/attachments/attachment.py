from typing import Hashable
import copy
import uuid
import time
from os.path import splitext

from sqlalchemy.ext.mutable import MutableDict

from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.typing import Attachable
from sqlalchemy_media.descriptors import AttachableDescriptor


class Attachment(MutableDict):
    __directory__ = 'attachments'
    __prefix__ = 'attachment'

    max_length = None
    min_length = None

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        StoreManager.observe_attribute(attribute)
        super()._listen_on_attribute(attribute, coerce, parent_cls)

    @classmethod
    def _assert_type(cls, value):
        """
        Checking attachment type, ignoring any type that not derived from :py:class:`Attachment`.
        :param value:
        :return:
        """
        if isinstance(value, Attachment) and not isinstance(value, cls):
            raise TypeError('Value type must be subclass of %s' % cls)

    @classmethod
    def coerce(cls, key, value):
        cls._assert_type(value)
        return super().coerce(key, value)

    @classmethod
    def create_from(cls, *args, **kwargs):
        instance = cls()
        instance.attach(*args, **kwargs)
        return instance

    def __hash__(self):
        return hash(self.key)

    @property
    def store_id(self):
        return self.get('storeId')

    @store_id.setter
    def store_id(self, value) -> None:
        self['storeId'] = value

    @property
    def key(self) -> Hashable:
        return self.get('key')

    @key.setter
    def key(self, value) -> None:
        self['key'] = value

    @property
    def empty(self):
        return self.key is None

    @property
    def path(self):
        return '%s/%s' % (self.__directory__, self.filename)

    @property
    def filename(self) -> str:
        return '%s-%s%s%s' % (self.__prefix__, self.key, self.suffix, self.extension if self.extension else '')

    @property
    def suffix(self):
        if self.original_filename:
            return '-%s' % splitext(self.original_filename)[0]
        return ''

    @property
    def extension(self) -> str:
        return self.get('extension')

    @extension.setter
    def extension(self, value) -> None:
        self['extension'] = value

    @property
    def content_type(self) -> str:
        return self.get('contentType')

    @content_type.setter
    def content_type(self, value) -> None:
        self['contentType'] = value

    @property
    def original_filename(self) -> str:
        return self.get('originalFilename')

    @original_filename.setter
    def original_filename(self, value) -> None:
        self['originalFilename'] = value

    @property
    def length(self) -> str:
        return self.get('length')

    @length.setter
    def length(self, value) -> None:
        self['length'] = value

    @property
    def timestamp(self):
        return self.get('timestamp')

    @timestamp.setter
    def timestamp(self, v):
        self['timestamp'] = v

    def copy(self):
        return self.__class__(copy.deepcopy(self))

    def get_store(self):
        store_manager = StoreManager.get_current_store_manager()
        return store_manager.get(self.store_id)

    def delete(self):
        self.get_store().delete(self.path)

    def attach(self, f: Attachable, content_type: str = None, original_filename: str = None, extension: str = None,
               store_id: str = None, overwrite: bool=False) -> None:

        # Wrap in AttachableDescriptor
        with AttachableDescriptor(
                f,
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
                self.original_filename = original_filename

            if descriptor.extension:
                self.extension = descriptor.extension

            if descriptor.content_type:
                self.content_type = descriptor.content_type

            if store_id is not None:
                self.store_id = store_id

            self['length'] = self.get_store().put(
                self.path,
                descriptor,
                max_length=self.max_length,
                min_length=self.min_length
            )

            self.timestamp = time.time()

            store_manager = StoreManager.get_current_store_manager()
            store_manager.register_to_delete_after_rollback(self)

            if old_attachment:
                store_manager.register_to_delete_after_commit(old_attachment)

    def locate(self):
        store = self.get_store()
        return '%s?_ts=%s' % (store.locate(self), self.timestamp)
