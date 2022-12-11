import unittest
from unittest import mock
from unittest.mock import Mock
from os.path import dirname, abspath, join

from google.cloud import storage

from sqlalchemy_media.stores.GoogleCloudStorage import GoogleCloudStorage
from sqlalchemy_media.tests.helpers import SqlAlchemyTestCase

FAKE_BUCKET = 'fake-bucket'
FAKE_CREDENTIALS = 'fake-credentials'
FAKE_REGION = 'fake-region'


class TestGoogleCloudStorageObject(SqlAlchemyTestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.this_dir = abspath(dirname(__file__))
        cls.stuff_path = join(cls.this_dir, 'stuff')
        cls.cat_jpeg = join(cls.stuff_path, 'cat.jpg')
        cls.cat_png = join(cls.stuff_path, 'cat.png')
        cls.cat_txt = join(cls.stuff_path, 'sample_text_file1.txt')
        super().setUpClass()

    @mock.patch('sqlalchemy_media.stores.GoogleCloudStorage.storage')
    def test_upload_file(self, mock_storage: storage):
        mock_storage.Client.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value.blob.return_value = Mock()

        gcs = GoogleCloudStorage(bucket=FAKE_BUCKET, service_account_json=FAKE_CREDENTIALS)

        with open(self.cat_jpeg, 'rb') as f:
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

    @mock.patch('sqlalchemy_media.stores.GoogleCloudStorage.storage')
    def test_get_url(self, mock_storage: storage):
        mock_storage.Client.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value.blob.return_value = Mock()

        gcs = GoogleCloudStorage(bucket=FAKE_BUCKET, service_account_json=FAKE_CREDENTIALS)
        gcs.locate('cat.jpg')

        mock_storage.Client.from_service_account_json.assert_called_once()
        mock_storage.Client.from_service_account_json.assert_called_with(FAKE_CREDENTIALS)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_with(FAKE_BUCKET)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob \
            .assert_called_with('cat.jpg')

    @mock.patch('sqlalchemy_media.stores.GoogleCloudStorage.storage')
    def test_open(self, mock_storage: storage):
        mock_storage.Client.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value.blob.return_value = Mock()

        gcs = GoogleCloudStorage(bucket=FAKE_BUCKET, service_account_json=FAKE_CREDENTIALS)
        gcs.open('cat.jpg')

        mock_storage.Client.from_service_account_json.assert_called_once()
        mock_storage.Client.from_service_account_json.assert_called_with(FAKE_CREDENTIALS)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.assert_called_with(FAKE_BUCKET)
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob.assert_called_once()
        mock_storage.Client.from_service_account_json.return_value.get_bucket.return_value.blob \
            .assert_called_with('cat.jpg')

    @mock.patch('sqlalchemy_media.stores.GoogleCloudStorage.storage')
    def test_delete(self, mock_storage: storage):
        mock_storage.Client.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value = Mock()
        mock_storage.Client.return_value.get_bucket.return_value.blob.return_value = Mock()

        gcs = GoogleCloudStorage(bucket=FAKE_BUCKET, service_account_json=FAKE_CREDENTIALS)
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
