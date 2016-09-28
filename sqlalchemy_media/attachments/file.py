from typing import Hashable
from os.path import splitext
import mimetypes
import uuid
import copy

from sqlalchemy.ext.mutable import MutableDict

from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.typing import Attachable
from sqlalchemy_media.constants import MB


class File(MutableDict):
    __directory__ = 'attachments'
    __prefix__ = 'attachment'

    max_length = 2*MB
    min_length = 0

    @property
    def store_manager(self):
        return StoreManager.get_current_store_manager()

    @property
    def path(self):
        return '%s/%s' % (self.__directory__, self.filename)

    @property
    def filename(self) -> str:
        return '%s-%s%s%s' % (self.__prefix__, self.key, self.suffix, self.extension)

    @property
    def suffix(self):
        if self.original_filename:
            return '-%s' % splitext(self.original_filename)[0]
        return ''

    @property
    def empty(self):
        return self.key is None

    def get_store(self):
        return self.store_manager.get(self.store_id)

    def store(self, f):
        length = self.get_store().put(self.path, f, max_length=self.max_length, min_length=self.min_length)
        self['length'] = length

    def delete(self):
        self.get_store().delete(self.path)

    def attach(self, f: Attachable, content_type: str=None, original_filename: str=None, extension: str=None,
               store_id: str=None) -> None:

        # Backup the old key and filename if exists
        old_attachment = None if self.empty else self.copy()

        # Determining original filename
        if original_filename is not None:
            self.original_filename = original_filename
        elif isinstance(f, str):
            self.original_filename = f

        # Determining the extension
        if extension is not None:
            self.extension = extension
        elif isinstance(f, str):
            self.extension = splitext(f)[1]
        elif original_filename is not None:
            self.extension = splitext(self.original_filename)[1]

        # Determining the mimetype
        if content_type is not None:
            self.content_type = content_type
        elif isinstance(f, str):
            self.content_type = mimetypes.guess_type(f)
        elif original_filename is not None:
            self.content_type = mimetypes.guess_type(self.original_filename)
        elif extension is not None:
            self.content_type = mimetypes.guess_type('x%s' % extension)

        self.key = str(uuid.uuid4())

        if store_id is not None:
            self.store_id = store_id

        self.store(f)
        self.store_manager.register_to_delete_after_rollback(self)
        if old_attachment:
            self.store_manager.register_to_delete_after_commit(old_attachment)

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

    def copy(self):
        return self.__class__(copy.deepcopy(self))

    @classmethod
    def _listen_on_attribute(cls, attribute, coerce, parent_cls):
        StoreManager.observe_attribute(attribute)
        super()._listen_on_attribute(attribute, coerce, parent_cls)
