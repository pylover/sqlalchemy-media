import threading
import contextlib
import io
import base64
from os import urandom
from os.path import split
from http.server import HTTPServer
from wsgiref.simple_server import WSGIServer

from sqlalchemy_media.mimetypes_ import guess_type


@contextlib.contextmanager
def simple_http_server(handler_class, server_class=HTTPServer, app=None, bind=('', 0)):
    server = server_class(bind, handler_class)
    if app:
        assert issubclass(server_class, WSGIServer)
        server.set_app(app)
    thread = threading.Thread(target=server.serve_forever, name='sa-media test server.', daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join()


def encode_multipart_data(fields: dict = None, files: dict = None):  # pragma: no cover
    boundary = ''.join(['-----', base64.urlsafe_b64encode(urandom(27)).decode()])
    crlf = b'\r\n'
    lines = []

    if fields:
        for key, value in fields.items():
            lines.append('--' + boundary)
            lines.append('Content-Disposition: form-data; name="%s"' % key)
            lines.append('')
            lines.append(value)

    if files:
        for key, file_path in files.items():
            filename = split(file_path)[1]
            lines.append('--' + boundary)
            lines.append(
                'Content-Disposition: form-data; name="%s"; filename="%s"' %
                (key, filename))
            lines.append(
                'Content-Type: %s' %
                (guess_type(filename) or 'application/octet-stream'))
            lines.append('')
            lines.append(open(file_path, 'rb').read())

    lines.append('--' + boundary + '--')
    lines.append('')

    body = io.BytesIO()
    length = 0
    for l in lines:
        # noinspection PyTypeChecker
        line = (l if isinstance(l, bytes) else l.encode()) + crlf
        length += len(line)
        body.write(line)
    body.seek(0)
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body, length