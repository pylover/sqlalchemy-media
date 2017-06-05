from typing import AnyStr
import io
from http.server import BaseHTTPRequestHandler, HTTPStatus

from sqlalchemy_media.typing_ import FileLike
from sqlalchemy_media.helpers import copy_stream
from sqlalchemy_media.mimetypes_ import guess_type
from .http import simple_http_server


def mockup_http_static_server(content: bytes = b'Simple file content.', content_type: str = None, **kwargs):
    class StaticMockupHandler(BaseHTTPRequestHandler):  # pragma: no cover
        def serve_text(self):
            self.send_header('Content-Type', "text/plain")
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Last-Modified', self.date_time_string())
            self.end_headers()
            self.wfile.write(content)

        def serve_static_file(self, filename: AnyStr):
            self.send_header('Content-Type', guess_type(filename))
            with open(filename, 'rb') as f:
                self.serve_stream(f)

        def serve_stream(self, stream: FileLike):
            buffer = io.BytesIO()
            self.send_header('Content-Length', str(copy_stream(stream, buffer)))
            self.end_headers()
            buffer.seek(0)
            try:
                copy_stream(buffer, self.wfile)
            except ConnectionResetError:
                pass

        # noinspection PyPep8Naming
        def do_GET(self):
            self.send_response(HTTPStatus.OK)
            if isinstance(content, bytes):
                self.serve_text()
            elif isinstance(content, str):
                self.serve_static_file(content)
            else:
                self.send_header('Content-Type', content_type)
                # noinspection PyTypeChecker
                self.serve_stream(content)

    return simple_http_server(StaticMockupHandler, **kwargs)
