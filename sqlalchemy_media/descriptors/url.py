
from urllib.request import urlopen

from sqlalchemy_media.descriptors.stream import CloserStreamDescriptor


class UrlDescriptor(CloserStreamDescriptor):
    def __init__(self, uri: str, content_type: str=None, original_filename: str=None, **kwargs):
        response = urlopen(uri)

        if content_type is None and 'Content-Type' in response.headers:
            content_type = response.headers.get('Content-Type')

        if 'Content-Length' in response.headers:
            kwargs['content_length'] = int(response.headers.get('Content-Length'))

        if original_filename is None:
            original_filename = uri

        super().__init__(response, content_type=content_type, original_filename=original_filename, **kwargs)
