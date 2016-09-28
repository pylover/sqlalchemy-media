
from sqlalchemy_media.attachments.attachment import Attachment
from sqlalchemy_media.constants import MB


class File(Attachment):

    max_length = 2*MB
    min_length = 0
