
from collections import Iterable
from sqlalchemy.ext.mutable import MutableList

from sqlalchemy_media.attachments.attachment import Attachment
from sqlalchemy_media.attachments.file import File


class AttachmentList(MutableList):
    __item_type__ = Attachment

    @classmethod
    def coerce(cls, index, value):

        if isinstance(value, Iterable):
            result = cls()
            for i in value:
                result.append(cls.__item_type__.coerce(index, i))
            return result

        return super().coerce(index, value)


class FileList(AttachmentList):
    __item_type__ = File
