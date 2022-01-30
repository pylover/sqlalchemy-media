import unittest
from unittest import mock
from unittest.mock import Mock

from google.cloud import storage

from sqlalchemy_media.stores.GoogleCloudStorge import GoogleCloudStorge
from sqlalchemy_media.tests.helpers import SqlAlchemyTestCase

FAKE_BUCKET = 'fake-bucket'
FAKE_CREDENTIALS = 'fake-credentials'
FAKE_REGION = 'fake-region'


class TestGoogleCloudStorgeObject(SqlAlchemyTestCase):
    @mock.patch('sqlalchemy_media.stores.gcp.storage')
    def test_upload_file(self, mock_storage: storage):
        mock_storage.Client.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value.blob.return_value = Mock()

        gcs = GoogleCloudStorge(bucket=FAKE_BUCKET, service_account_json=FAKE_CREDENTIALS)

        with open('stuff/cat.jpg', 'rb') as f:
            length = gcs.put(filename='cat.jpg', stream=f)

            self.assertEqual(length, 70279)
            mock_storage.Client.from_service_account_json.assert_called_once()
            mock_storage.Client.from_service_account_json.assert_called_with(FAKE_CREDENTIALS)
            mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_once()
            mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_with(FAKE_BUCKET)
            mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob.assert_called_once()
            mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob \
                .assert_called_with('cat.jpg')
            mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob.return_value. \
                upload_from_string.assert_called_once()

    @mock.patch('sqlalchemy_media.stores.gcp.storage')
    def test_get_url(self, mock_storage: storage):
        mock_storage.Client.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value.blob.return_value = Mock()

        gcs = GoogleCloudStorge(bucket=FAKE_BUCKET, service_account_json=FAKE_CREDENTIALS)
        gcs.locate('cat.jpg')

        mock_storage.Client.from_service_account_json.assert_called_once()
        mock_storage.Client.from_service_account_json.assert_called_with(FAKE_CREDENTIALS)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_with(FAKE_BUCKET)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob \
            .assert_called_with('cat.jpg')

    @mock.patch('sqlalchemy_media.stores.gcp.storage')
    def test_open(self, mock_storage: storage):
        mock_storage.Client.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value.blob.return_value = Mock()

        gcs = GoogleCloudStorge(bucket=FAKE_BUCKET, service_account_json=FAKE_CREDENTIALS)
        gcs.open('cat.jpg')

        mock_storage.Client.from_service_account_json.assert_called_once()
        mock_storage.Client.from_service_account_json.assert_called_with(FAKE_CREDENTIALS)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_with(FAKE_BUCKET)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob \
            .assert_called_with('cat.jpg')

    @mock.patch('sqlalchemy_media.stores.gcp.storage')
    def test_delete(self, mock_storage: storage):
        mock_storage.Client.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value.blob.return_value = Mock()

        gcs = GoogleCloudStorge(bucket=FAKE_BUCKET, service_account_json=FAKE_CREDENTIALS)
        gcs.delete('cat.jpg')

        mock_storage.Client.from_service_account_json.assert_called_once()
        mock_storage.Client.from_service_account_json.assert_called_with(FAKE_CREDENTIALS)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_with(FAKE_BUCKET)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob \
            .assert_called_with('cat.jpg')


if __name__ == '__main__':
    unittest.main()
