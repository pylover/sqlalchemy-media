from typing import Hashable
import mimetypes
import uuid
from os.path import splitext

from sqlalchemy.ext.mutable import MutableDict

from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.typing import Attachable


class Attachment(MutableDict):
    __directory__ = 'attachments'
    __prefix__ = 'attachment'

    _files_to_remove = []

    @property
    def store_manager(self):
        return StoreManager.get_current_store_manager()

    @property
    def store_id(self):
        return self.get('store_id')

    @property
    def store(self):
        return self.store_manager.get(self.store_id)

    def commit(self):
        if self._files_to_remove:
            for f in self._files_to_remove:
                f.delete()

    @property
    def path(self):
        return '%s/%s' % (self.__directory__, self.filename)

    @property
    def key(self) -> Hashable:
        return self.get('key')

    @property
    def filename(self) -> str:
        return '%s-%s%s' % (self.__prefix__, self.key, self.extension)

    @property
    def extension(self) -> str:
        return self.get('extension', '')

    @property
    def content_type(self) -> str:
        return self.get('contentType')

    @content_type.setter
    def content_type(self, v) -> str:
        self['contentType'] = v

    @property
    def original_filename(self) -> str:
        return self.get('originalFilename')

    def attach(self, f: Attachable, content_type: str=None, original_filename: str=None, extension: str=None,
               store_id: str=None) -> None:
        # Backup the old key and filename if exists
        old_path = self.path if self.key is not None else None

        # Determining original filename
        if original_filename is not None:
            self['originalFilename'] = original_filename
        elif isinstance(f, str):
            self['originalFilename'] = f

        # Determining the extension
        if extension is not None:
            self['extension'] = extension
        elif isinstance(f, str):
            self['extension'] = splitext(f)[1]
        elif original_filename is not None:
            self['extension'] = splitext(self.original_filename)[1]

        # Determining the mimetype
        if content_type is not None:
            self['contentType'] = content_type
        elif isinstance(f, str):
            self['contentType'] = mimetypes.guess_type(f)
        elif original_filename is not None:
            self['contentType'] = mimetypes.guess_type(self.original_filename)
        elif extension is not None:
            self['contentType'] = mimetypes.guess_type('x%s' % extension)

        self['key'] = str(uuid.uuid4())

        if store_id is not None:
            self['storeId'] = store_id

        length = self.store.put(self.path, f)
        self['length'] = length
