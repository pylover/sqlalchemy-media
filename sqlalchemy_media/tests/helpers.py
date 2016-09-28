from typing import Tuple
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
import contextlib
import json

from sqlalchemy import Unicode, TypeDecorator


Address = Tuple[str, int]


@contextlib.contextmanager
def simple_http_server(content: bytes= b'Simple file content.', bind: Address=('', 0)):

    class SimpleHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', "text/plain")
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Last-Modified', self.date_time_string())
            self.end_headers()
            self.wfile.write(content)

    http_server = HTTPServer(bind, SimpleHandler)
    thread = threading.Thread(target=http_server.serve_forever, name='sa-media test server.', daemon=True)
    thread.start()
    yield http_server
    http_server.shutdown()
    thread.join()


# noinspection PyAbstractClass
class Json(TypeDecorator):
    impl = Unicode

    def process_bind_param(self, value, engine):
        return json.dumps(value)

    def process_result_value(self, value, engine):
        if value is None:
            return None

        return json.loads(value)


if __name__ == '__main__':
    with simple_http_server(bind=('', 8080), content=b'simple text') as httpd:
        target_url = 'http://%s:%s' % httpd.server_address
        print(target_url)
        time.sleep(1)
