from io import BytesIO

# Importing optional stuff required by http based store
try:
    # noinspection PyPackageRequirements
    import requests
except ImportError:  # pragma: no cover
    requests = None


# Importing optional stuff required by OS2 store
try:
    # noinspection PyPackageRequirements
    from aliyunauth import OssAuth as OS2Auth
except ImportError:  # pragma: no cover
    OS2Auth = None


from sqlalchemy_media.exceptions import OS2Error
from sqlalchemy_media.optionals import ensure_os2auth
from sqlalchemy_media.typing_ import FileLike
from .base import Store


class OS2Store(Store):
    """
    Store for dealing with oss of aliyun

    """
    base_url = 'https://{0}.oss-{1}.aliyuncs.com'

    DEFAULT_MAX_AGE = 60 * 60 * 24 * 365

    def __init__(self, bucket: str, access_key: str, secret_key: str,
                 region: str, max_age: int = DEFAULT_MAX_AGE,
                 base_headers: dict = None, prefix: str = None,
                 base_url: str = None, cdn_url: str = None, cdn_prefix_ignore: bool = False,
                 acl: str = 'private'):
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.max_age = max_age
        self.prefix = prefix
        self.acl = acl
        self.base_headers = base_headers or {}

        if base_url:
            self.base_url = base_url
        else:
            self.base_url = self.base_url.format(bucket, region)

        if prefix:
            self.base_url = '%s/%s' % (self.base_url, prefix)
            if cdn_url and not cdn_prefix_ignore:
                cdn_url = '%s/%s' % (cdn_url, prefix)

        if self.base_url.endswith('/'):
            self.base_url = self.base_url.rstrip('/')
        if cdn_url and cdn_url.endswith('/'):
            cdn_url = cdn_url.rstrip('/')

        self.cdn_url = cdn_url

    def _get_os2_url(self, filename: str):
        return '{0}/{1}'.format(self.base_url, filename)

    def _upload_file(self, url: str, data: str, content_type: str):
        ensure_os2auth()

        auth = OS2Auth(self.bucket, self.access_key, self.secret_key)
        headers = self.base_headers.copy()
        headers.update({
            'Cache-Control': 'max-age=' + str(self.max_age),
            'x-oss-object-acl': self.acl
        })
        if content_type:
            headers['Content-Type'] = content_type
        res = requests.put(url, auth=auth, data=data, headers=headers)
        if not 200 <= res.status_code < 300:
            raise OS2Error(res.text)

    def put(self, filename: str, stream: FileLike):
        url = self._get_os2_url(filename)
        data = stream.read()
        content_type = getattr(stream, 'content_type', None)
        self._upload_file(url, data, content_type)
        return len(data)

    def delete(self, filename: str):
        ensure_os2auth()
        url = self._get_os2_url(filename)
        auth = OS2Auth(self.bucket, self.access_key, self.secret_key)
        headers = self.base_headers.copy()
        res = requests.delete(url, auth=auth, headers=headers)
        if not 200 <= res.status_code < 300:
            raise OS2Error(res.text)

    def open(self, filename: str, mode: str='rb') -> FileLike:
        ensure_os2auth()
        url = self._get_os2_url(filename)
        auth = OS2Auth(self.bucket, self.access_key, self.secret_key)
        headers = self.base_headers.copy()
        res = requests.get(url, auth=auth, headers=headers)
        if not 200 <= res.status_code < 300:
            raise OS2Error(res.text)
        return BytesIO(res.content)

    def locate(self, attachment) -> str:
        if self.cdn_url:
            base_url = self.cdn_url
        else:
            base_url = self.base_url
        return '%s/%s' % (base_url, attachment.path)
