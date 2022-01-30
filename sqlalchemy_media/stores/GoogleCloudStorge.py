""""
    Google cloud storage
"""
from io import BytesIO

from google.cloud import storage
from google.cloud.exceptions import NotFound

from sqlalchemy_media.exceptions import GCPError
from sqlalchemy_media.optionals import ensure_gcs
from .base import Store
from ..typing_ import FileLike


class GoogleCloudStorge(Store):
    """
    Google Cloud Storage Implements Store base.
    """

    def __init__(self, bucket: str, service_account_json: str, acl: str = 'private'):
        """
        Initialize GoogleCloudStorge
        :param bucket: bucket name
        :param service_account_json: service account json file(credential)
        :param acl: public or private
        """
        self.bucket = bucket
        self._storage_client = storage.Client.from_service_account_json(service_account_json)
        self.acl = acl

    def _get_or_create_bucket(self):
        """
        Get bucket if exist else create a bucket
        :return bucket object
        """
        ensure_gcs()
        try:
            return self._storage_client.get_bucket(self.bucket)
        except NotFound:
            return self._storage_client.create_bucket(self.bucket)

    def _upload_file(self, file_name: str, data: str):
        """
        Create a blob and upload file,
        add acl if needed
        """
        ensure_gcs()
        try:
            bucket = self._get_or_create_bucket()
            blob = bucket.blob(file_name)
            blob.upload_from_string(data)
            if self.acl == 'public':
                blob.make_public()
        except Exception as e:
            raise GCPError(e)

    def locate(self, attachment) -> str:
        """
        Get Download link of a file by its name
        """
        ensure_gcs()
        try:
            bucket = self._get_or_create_bucket()
            return bucket.blob(attachment).public_url
        except Exception as e:
            raise GCPError(e)

    def open(self, filename: str, mode: str = 'rb') -> FileLike:
        """
        Download a file as byte
        """
        ensure_gcs()
        try:
            bucket = self._get_or_create_bucket()
            blob = bucket.blob(filename)
            file_byte = blob.download_to_filename()
            return BytesIO(bytes(file_byte))
        except Exception as e:
            raise GCPError(e)

    def delete(self, filename: str) -> None:
        """
        Delete a file by its name
        """
        ensure_gcs()
        try:
            bucket = self._get_or_create_bucket()
            blob = bucket.blob(filename)
            blob.delete()
        except Exception as e:
            raise GCPError(e)

    def put(self, filename: str, stream: FileLike) -> int:
        """
        Put files into Google cloud storage
        """
        ensure_gcs()
        data = stream.read()
        self._upload_file(filename, data)
        return len(data)
