from typing import Hashable
import mimetypes
import uuid
import copy
from os.path import splitext

from sqlalchemy.ext.mutable import MutableDict

from sqlalchemy_media.stores import StoreManager
from sqlalchemy_media.typing import Attachable


class Attachment(MutableDict):
    __directory__ = 'attachments'
    __prefix__ = 'attachment'

    def __init__(self, *args, **kwr):
        self._files_to_remove = []
        self._files_added = []
        super(Attachment, self).__init__(*args, **kwr)

    @property
    def store_manager(self):
        return StoreManager.get_current_store_manager()

    @property
    def store_id(self):
        return self.get('store_id')

    @property
    def store(self):
        return self.store_manager.get(self.store_id)

    @property
    def path(self):
        return '%s/%s' % (self.__directory__, self.filename)

    @property
    def key(self) -> Hashable:
        return self.get('key')

    @property
    def filename(self) -> str:
        return '%s-%s%s%s' % (self.__prefix__, self.key, self.suffix, self.extension)

    @property
    def suffix(self):
        if self.original_filename:
            return '-%s' % splitext(self.original_filename)[0]

    @property
    def extension(self) -> str:
        return self.get('extension', '')

    @property
    def content_type(self) -> str:
        return self.get('contentType')

    @property
    def original_filename(self) -> str:
        return self.get('originalFilename')

    @property
    def empty(self):
        return self.key is None

    def copy(self):
        return self.__class__(copy.deepcopy(self))

    def commit(self):
        for f in self._files_to_remove:
            f.delete()
        self._reset_state()

    def rollback(self):
        for f in self._files_added:
            f.delete()
        self._reset_state()

    def _reset_state(self):
        self._files_to_remove = []
        self._files_added = []

    def attach(self, f: Attachable, content_type: str=None, original_filename: str=None, extension: str=None,
               store_id: str=None) -> None:
        # Backup the old key and filename if exists
        if not self.empty:
            self._files_to_remove.append(self.copy())

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

    def delete(self):
        self.store.delete(self.path)
