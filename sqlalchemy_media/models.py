from typing import TypeVar, Generic
import mimetypes
import uuid
from os.path import splitext

from sqlalchemy.ext.mutable import MutableDict, Mutable

from sqlalchemy_media.stores import Store, current_store
from sqlalchemy_media.typing import Attachable, AttachmentKey


T = TypeVar('T')


class Attachment(MutableDict, Generic[T]):

    __directory__ = 'attachments'
    __prefix__ = 'attachment'

    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionary to instance of this class."""
        if not isinstance(value, cls):
            if isinstance(value, dict):
                return cls(value)
            return Mutable.coerce(key, value)
        else:
            return value

    @property
    def path(self):
        return '%s/%s' % (self.__directory__, self.filename)

    @property
    def key(self):
        return self.get('key')

    @property
    def filename(self):
        return '%s-%s%s' % (self.__prefix__, self.key, self.extension)

    @property
    def extension(self):
        return self.get('extension', '')

    @property
    def content_type(self):
        return self.get('contentType')

    @content_type.setter
    def content_type(self, v):
        self['contentType'] = v

    @property
    def original_filename(self):
        return self.get('originalFilename')

    def attach(self, f: Attachable, content_type: str=None, original_filename: str=None, extension: str=None,
               store: Store=current_store) -> T:
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

        length = store.put(self.path, f)
        self['length'] = length

        return self

