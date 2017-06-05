from io import BytesIO

# Importing optional stuff required by http based store
try:
    # noinspection PyPackageRequirements
    import requests
except ImportError:  # pragma: no cover
    requests = None


# Importing optional stuff required by S3 store
try:
    # noinspection PyPackageRequirements
    from requests_aws4auth import AWS4Auth
except ImportError:  # pragma: no cover
    AWS4Auth = None

from sqlalchemy_media.exceptions import S3Error
from sqlalchemy_media.optionals import ensure_aws4auth
from sqlalchemy_media.typing_ import FileLike
from .base import Store


DEFAULT_MAX_AGE = 60 * 60 * 24 * 365


class S3Store(Store):
    """
    Store for dealing with s3 of aws

    .. versionadded:: 0.9.0

    .. versionadded:: 0.9.6

       - ``prefix``

    """
    base_url = 'https://{0}.s3.amazonaws.com'

    def __init__(self, bucket: str, access_key: str, secret_key: str,
                 region: str, max_age: int = DEFAULT_MAX_AGE,
                 prefix: str = None, base_url: str = None):
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.max_age = max_age
        self.prefix = prefix
        self.base_url = self.base_url.format(bucket)

        if base_url:
            self.base_url = base_url

        if prefix:
            self.base_url = '{0}/{1}'.format(self.base_url, prefix)

        if self.base_url.endswith('/'):
            self.base_url = self.base_url.rstrip('/')

    def _get_s3_url(self, filename: str):
        return '{0}/{1}'.format(self.base_url, filename)

    def _upload_file(self, url: str, data: str, content_type: str,
                     rrs: bool = False, acl: str = 'private'):
        ensure_aws4auth()

        auth = AWS4Auth(self.access_key, self.secret_key, self.region, 's3')
        if rrs:
            storage_class = 'REDUCED_REDUNDANCY'
        else:
            storage_class = 'STANDARD'
        headers = {
            'Cache-Control': 'max-age=' + str(self.max_age),
            'x-amz-acl': acl,
            'x-amz-storage-class': storage_class
        }
        if content_type:
            headers['Content-Type'] = content_type
        res = requests.put(url, auth=auth, data=data, headers=headers)
        if not 200 <= res.status_code < 300:
            raise S3Error(res.text)

    def put(self, filename: str, stream: FileLike):
        url = self._get_s3_url(filename)
        data = stream.read()
        content_type = getattr(stream, 'content_type', None)
        rrs = getattr(stream, 'reproducible', False)
        self._upload_file(url, data, content_type, rrs=rrs)
        return len(data)

    def delete(self, filename: str):
        ensure_aws4auth()
        url = self._get_s3_url(filename)
        auth = AWS4Auth(self.access_key, self.secret_key, self.region, 's3')
        res = requests.delete(url, auth=auth)
        if not 200 <= res.status_code < 300:
            raise S3Error(res.text)

    def open(self, filename: str, mode: str='rb') -> FileLike:
        ensure_aws4auth()
        url = self._get_s3_url(filename)
        auth = AWS4Auth(self.access_key, self.secret_key, self.region, 's3')
        res = requests.get(url, auth=auth)
        if not 200 <= res.status_code < 300:
            raise S3Error(res.text)
        return BytesIO(res.content)

    def locate(self, attachment) -> str:
        return '%s/%s' % (self.base_url, attachment.path)
