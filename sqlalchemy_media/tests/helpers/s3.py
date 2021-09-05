import contextlib
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer

import httpx

from sqlalchemy_media.stores import S3Store

from .config import TEST_ACCESS_KEY, TEST_BUCKET, TEST_REGION, TEST_SECRET_KEY
from .http import simple_http_server


@contextlib.contextmanager
def mockup_s3_server(bucket, **kwargs):
    from moto.server import DomainDispatcherApplication, create_backend_app
    mock_app = DomainDispatcherApplication(create_backend_app, 's3')
    mock_app.debug = False
    with simple_http_server(
        WSGIRequestHandler,
        server_class=WSGIServer,
        app=mock_app,
        **kwargs
    ) as server:
        url = 'http://localhost:%s' % server.server_address[1]
        # Create the bucket
        bucket_uri = '%s/%s' % (url, bucket)
        res = httpx.put(bucket_uri)
        assert res.status_code == 200
        yield server, bucket_uri


def create_s3_store(bucket=TEST_BUCKET, **kwargs):
    return S3Store(
        bucket,
        TEST_ACCESS_KEY,
        TEST_SECRET_KEY,
        TEST_REGION,
        **kwargs
    )
