
from urllib.request import urlopen

from sqlalchemy_media.descriptors.stream import CloserStreamDescriptor


class UrlDescriptor(CloserStreamDescriptor):
    def __init__(self, uri: str, content_type: str=None, **kwargs):
        self.original_filename = uri
        response = urlopen(uri)

        if content_type is None and 'Content-Type' in response.headers:
            content_type = response.headers.get('Content-Type')

        if 'Content-Length' in response.headers:
            kwargs['content_length'] = int(response.headers.get('Content-Length'))

        super().__init__(response, content_type = content_type, ** kwargs)

