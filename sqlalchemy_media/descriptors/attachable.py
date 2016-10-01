
import cgi

from sqlalchemy_media.typing import Attachable
from sqlalchemy_media.helpers import is_uri
from sqlalchemy_media.descriptors.base import BaseDescriptor
from sqlalchemy_media.descriptors.localfs import LocalFileSystemDescriptor
from sqlalchemy_media.descriptors.cgi_fieldstorage import CgiFieldStorageDescriptor
from sqlalchemy_media.descriptors.url import UrlDescriptor
from sqlalchemy_media.descriptors.stream import StreamDescriptor


# noinspection PyAbstractClass
class AttachableDescriptor(BaseDescriptor):

    # noinspection PyInitNewSignature
    def __new__(cls, attachable: Attachable, *args, **kwargs):
        """
        Should determine the appropriate descriptor and return an instance of it.
        :param attachable:
        :param args:
        :param kwargs:
        :return:
        """

        if isinstance(attachable, cgi.FieldStorage):
            return_type = CgiFieldStorageDescriptor
        elif isinstance(attachable, str):
            return_type = UrlDescriptor if is_uri(attachable) else LocalFileSystemDescriptor
        else:
            return_type = StreamDescriptor

        return return_type(attachable, *args, **kwargs)

