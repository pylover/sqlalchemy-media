
from os import remove, makedirs
from os.path import join, exists, split
import contextlib
from wsgiref.simple_server import WSGIServer
from http.server import BaseHTTPRequestHandler, HTTPStatus

from sqlalchemy_media.helpers import copy_stream

from .http import simple_http_server


@contextlib.contextmanager
def mockup_os2_server(temp_path, bucket, **kwargs):
    class OS2Handler(BaseHTTPRequestHandler):  # pragma: no cover

        def _validate_host(self):
            host = self.headers['HOST']
            try:
                bucket, region, *_ = host.split('.')
            except ValueError:
                return self.send_error(400, 'BadRequest')
            if region != 'oss-sa-media':
                return self.send_error(400, 'BadRegionError')
            if not exists(join(temp_path, bucket)):
                return self.send_error(400, 'BadBucketError')
            return bucket, region

        # noinspection PyPep8Naming
        def do_GET(self):
            try:
                bucket, _ = self._validate_host()
            except TypeError:
                return
            if self.path == '/':
                return self.send_error('400', 'BadObjectError')

            filename = join(temp_path, bucket, self.path[1:])
            if not exists(filename):
                return self.send_error(404, 'NotFound')

            self.send_response(HTTPStatus.OK)
            with open(filename, 'rb') as f:
                data = f.read()
                self.send_header('Content-Length', len(data))
                self.end_headers()
                f.seek(0)
                try:
                    copy_stream(f, self.wfile)
                except ConnectionResetError:
                    pass

        # noinspection PyPep8Naming
        def do_PUT(self):
            try:
                bucket, _ = self._validate_host()
            except TypeError:
                return
            if self.path == '/':
                return self.send_error('400', 'BadObjectError')
            filename = self.path[1:]
            content_len = int(self.headers.get('content-length', 0))
            content = self.rfile.read(content_len)
            filename = join(temp_path, bucket, filename)
            # path = '/'.join(filename.split('/')[:-1])
            path = split(filename)[0]
            # Remove previous files, if any! to make a clean temp directory:
            if not exists(path):  # pragma: no cover
                makedirs(path)

            with open(filename, 'wb') as f:
                f.write(content)
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', "text/plain")
            self.end_headers()

        # noinspection PyPep8Naming
        def do_DELETE(self):
            try:
                bucket, _ = self._validate_host()
            except TypeError:
                return
            if self.path == '/':
                return self.send_error('400', 'BadObjectError')

            filename = join(temp_path, bucket, self.path[1:])
            if not exists(filename):
                return self.send_error(404, 'NotFound')

            remove(filename)
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', "text/plain")
            self.end_headers()

    # Ensure bucket
    makedirs(join(temp_path, bucket), exist_ok=True)
    with simple_http_server(OS2Handler,  server_class=WSGIServer, **kwargs) as server:
        url = 'http://localhost:%s' % server.server_address[1]
        yield server, url
