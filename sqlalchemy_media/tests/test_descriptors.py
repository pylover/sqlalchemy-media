
import unittest
import io
import cgi
from os.path import dirname, abspath, join, split

from sqlalchemy_media.helpers import copy_stream, md5sum
from sqlalchemy_media.tests.helpers import simple_http_server, encode_multipart_data
from sqlalchemy_media.descriptors import AttachableDescriptor, LocalFileSystemDescriptor, CgiFieldStorageDescriptor, \
    UrlDescriptor


class AttachableDescriptorsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')
        cls.cat_jpeg = join(cls.stuff_path, 'cat.jpg')

    def test_localfs(self):

        descriptor = AttachableDescriptor(self.cat_jpeg)
        self.assertIsInstance(descriptor, LocalFileSystemDescriptor)
        self.assertEqual(descriptor.content_type, 'image/jpeg')  # Must be determined from the file's extension: .jpg
        self.assertEqual(descriptor.original_filename, self.cat_jpeg)

        buffer = io.BytesIO()
        copy_stream(descriptor, buffer)
        buffer.seek(0)
        self.assertEqual(md5sum(buffer), md5sum(self.cat_jpeg))

    def test_url(self):

        with simple_http_server(self.cat_jpeg) as http_server:
            url = 'http://%s:%s' % http_server.server_address
            descriptor = AttachableDescriptor(url)

            self.assertIsInstance(descriptor, UrlDescriptor)
            self.assertEqual(descriptor.content_type, 'image/jpeg')  # Must be determined from response headers
            self.assertEqual(descriptor.content_length, 70279)  # Must be determined from response headers
            self.assertEqual(descriptor.original_filename, url)

    def test_cgi_field_storage(self):
        # encode a multipart form
        content_type, body, content_length = encode_multipart_data(files=dict(cat=self.cat_jpeg))
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': content_type,
            'CONTENT_LENGTH': content_length
        }

        storage = cgi.FieldStorage(body, environ=environ)

        descriptor = AttachableDescriptor(storage['cat'])
        self.assertIsInstance(descriptor, CgiFieldStorageDescriptor)
        self.assertEqual(descriptor.content_type, 'image/jpeg')
        self.assertEqual(descriptor.original_filename, split(self.cat_jpeg)[1])

        buffer = io.BytesIO()
        copy_stream(descriptor, buffer)
        buffer.seek(0)
        self.assertEqual(md5sum(buffer), md5sum(self.cat_jpeg))


if __name__ == '__main__':
    unittest.main()
