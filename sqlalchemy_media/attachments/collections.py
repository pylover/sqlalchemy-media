
from sqlalchemy.ext.mutable import MutableList

from sqlalchemy_media.attachments.attachment import Attachment
from sqlalchemy_media.attachments.file import File


class AttachmentList(MutableList):
    __item_type__ = Attachment


class FileList(AttachmentList):
    __item_type__ = File
