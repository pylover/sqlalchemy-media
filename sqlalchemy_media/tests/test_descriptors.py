
import unittest
import io
import cgi
from os.path import dirname, abspath, join, split

from sqlalchemy_media.helpers import copy_stream, md5sum
from sqlalchemy_media.tests.helpers import mockup_http_static_server, encode_multipart_data
from sqlalchemy_media.descriptors import AttachableDescriptor, LocalFileSystemDescriptor, CgiFieldStorageDescriptor, \
    UrlDescriptor, StreamDescriptor
from sqlalchemy_media.exceptions import MaximumLengthIsReachedError, DescriptorOperationError


class AttachableDescriptorsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')
        cls.cat_jpeg = join(cls.stuff_path, 'cat.jpg')
        cls.dog_jpeg = join(cls.stuff_path, 'dog.jpg')

    def test_stream(self):
        # guess content types from extension
        descriptor = AttachableDescriptor(io.BytesIO(b'Simple text'), extension='.txt')
        self.assertIsInstance(descriptor, StreamDescriptor)
        self.assertEqual(descriptor.content_type, 'text/plain')
        descriptor.seek(2)
        self.assertEqual(descriptor.tell(), 2)

        # guess extension from original filename
        descriptor = AttachableDescriptor(io.BytesIO(b'Simple text'), original_filename='letter.pdf')
        self.assertEqual(descriptor.extension, '.pdf')

        # guess extension from content type
        descriptor = AttachableDescriptor(io.BytesIO(b'Simple text'), content_type='application/json')
        self.assertEqual(descriptor.extension, '.json')

        self.assertRaises(DescriptorOperationError, lambda: descriptor.filename)

    def test_non_seekable(self):

        class NonSeekableStream(io.BytesIO):

            def seekable(self, *args, **kwargs):
                return False

        inp = b'abcdefghijklmnopqrstuvwxyz'
        descriptor = AttachableDescriptor(NonSeekableStream(inp), header_buffer_size=10)

        # fetching header, it forces to cache header_buffer_size bytes from header.
        buffer = descriptor.get_header_buffer()
        self.assertEqual(buffer, b'abcdefghij')

        # fetching again to test the cache functionality
        buffer = descriptor.get_header_buffer()
        self.assertEqual(buffer, b'abcdefghij')

        out = b''
        out += descriptor.read(9)
        self.assertEqual(descriptor.tell(), 9)
        out += descriptor.read(11)
        self.assertEqual(descriptor.tell(), 20)
        out += descriptor.read(10)
        self.assertEqual(out, inp)

        # Max length error
        descriptor = AttachableDescriptor(NonSeekableStream(inp), header_buffer_size=24, max_length=20)
        buffer = descriptor.get_header_buffer()
        self.assertEqual(buffer, b'abcdefghijklmnopqrstuvwx')
        self.assertRaises(MaximumLengthIsReachedError, descriptor.read, 1)

        # Test getting header buffer after read on non-seekable streams.
        descriptor = AttachableDescriptor(NonSeekableStream(inp), header_buffer_size=10, max_length=20)
        self.assertEqual(descriptor.read(10), b'abcdefghij')
        self.assertRaises(DescriptorOperationError, descriptor.get_header_buffer)

    def test_localfs(self):

        descriptor = AttachableDescriptor(self.cat_jpeg, width=100, height=80)
        self.assertIsInstance(descriptor, LocalFileSystemDescriptor)
        self.assertEqual(descriptor.filename, self.cat_jpeg)

        # Must be determined from the given file's extension: .jpg
        self.assertEqual(descriptor.content_type, 'image/jpeg')
        self.assertEqual(descriptor.original_filename, self.cat_jpeg)

        # noinspection PyUnresolvedReferences
        self.assertEqual(descriptor.width, 100)
        # noinspection PyUnresolvedReferences
        self.assertEqual(descriptor.height, 80)

        self.assertEqual(len(descriptor.get_header_buffer()), 1024)

        buffer = io.BytesIO()
        copy_stream(descriptor, buffer)
        buffer.seek(0)
        self.assertEqual(md5sum(buffer), md5sum(self.cat_jpeg))

    def test_url(self):

        with mockup_http_static_server(self.cat_jpeg) as http_server:
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

    def test_force_seekable(self):

        with mockup_http_static_server(self.cat_jpeg) as http_server:
            url = 'http://%s:%s' % http_server.server_address
            original_sum = md5sum(self.cat_jpeg)

            with AttachableDescriptor(url) as descriptor:
                descriptor.prepare_to_read(backend='file')
                self.assertEqual(original_sum, md5sum(descriptor))

            with AttachableDescriptor(url) as descriptor:
                descriptor.prepare_to_read(backend='temp')
                self.assertEqual(original_sum, md5sum(descriptor))

            with AttachableDescriptor(url) as descriptor:
                descriptor.prepare_to_read(backend='memory')
                self.assertEqual(original_sum, md5sum(descriptor))

            with AttachableDescriptor(url) as descriptor:
                # Reading some bytes, before making the stream seekable
                descriptor.get_header_buffer()
                descriptor.prepare_to_read(backend='temp')
                self.assertEqual(original_sum, md5sum(descriptor))

            with AttachableDescriptor(url) as descriptor:
                self.assertRaises(DescriptorOperationError, descriptor.prepare_to_read, backend='InvalidBackend')

            with open(self.dog_jpeg, 'rb') as f, AttachableDescriptor(url) as descriptor:
                descriptor.replace(f, position=1024)

            with open(self.dog_jpeg, 'rb') as f, AttachableDescriptor(url) as descriptor:
                descriptor.replace(f)
                self.assertEqual(md5sum(descriptor), md5sum(self.dog_jpeg))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
