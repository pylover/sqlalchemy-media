

from sqlalchemy_media.attachments.file import File
from sqlalchemy_media.constants import MB, KB


class Image(File):
    __directory__ = 'images'
    __prefix__ = 'image'

    max_length = 2*MB
    min_length = 4*KB
