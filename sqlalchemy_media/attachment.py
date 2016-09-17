from typing import Hashable
from os.path import splitext
import mimetypes
import uuid

from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.typing import Attachable


class Attachment(object):
    __directory__ = 'attachments'
    __prefix__ = 'attachment'

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
        length = self.get_store().put(self.path, f)
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
        raise NotImplementedError

    @store_id.setter
    def store_id(self, value) -> None:
        raise NotImplementedError

    @property
    def key(self) -> Hashable:
        raise NotImplementedError

    @key.setter
    def key(self, value) -> None:
        raise NotImplementedError

    @property
    def extension(self) -> str:
        raise NotImplementedError

    @extension.setter
    def extension(self, value) -> None:
        raise NotImplementedError

    @property
    def content_type(self) -> str:
        raise NotImplementedError

    @content_type.setter
    def content_type(self, value) -> None:
        raise NotImplementedError

    @property
    def original_filename(self) -> str:
        raise NotImplementedError

    @original_filename.setter
    def original_filename(self, value) -> None:
        raise NotImplementedError

    @property
    def length(self) -> str:
        raise NotImplementedError

    @length.setter
    def length(self, value) -> None:
        raise NotImplementedError

    def copy(self) -> 'Attachment':
        raise NotImplementedError
