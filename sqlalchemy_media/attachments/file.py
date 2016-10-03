
from sqlalchemy_media.attachments.attachment import Attachment
from sqlalchemy_media.constants import MB


class File(Attachment):

    __max_length__ = 2 * MB
    __min_length__ = 0
