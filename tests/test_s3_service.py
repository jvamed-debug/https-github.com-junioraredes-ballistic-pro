"""Tests for services.s3_service — S3 upload/delete with mocked boto3."""

import pytest
from unittest.mock import patch, MagicMock


class TestS3ServiceInit:
    @patch("services.s3_service.boto3")
    @patch("services.s3_service.st")
    def test_init_with_valid_config(self, mock_st, mock_boto3):
        mock_st.secrets.get.return_value = {
            "bucket_name": "test-bucket",
            "region_name": "us-west-2",
            "aws_access_key_id": "AKID",
            "aws_secret_access_key": "SECRET",
        }
        from services.s3_service import S3Service
        svc = S3Service()
        assert svc.client is not None
        assert svc.bucket_name == "test-bucket"
        assert svc.region == "us-west-2"

    @patch("services.s3_service.boto3")
    @patch("services.s3_service.st")
    def test_init_without_bucket_name(self, mock_st, mock_boto3):
        mock_st.secrets.get.return_value = {}
        from services.s3_service import S3Service
        svc = S3Service()
        assert svc.client is None

    @patch("services.s3_service.boto3")
    @patch("services.s3_service.st")
    def test_init_handles_exception(self, mock_st, mock_boto3):
        mock_st.secrets.get.side_effect = Exception("no secrets")
        from services.s3_service import S3Service
        svc = S3Service()
        assert svc.client is None


class TestUploadImage:
    def _make_service(self):
        svc = MagicMock()
        svc.client = MagicMock()
        svc.bucket_name = "test-bucket"
        svc.region = "us-east-1"
        from services.s3_service import S3Service
        svc.upload_image = S3Service.upload_image.__get__(svc)
        return svc

    def test_upload_returns_url(self):
        svc = self._make_service()
        mock_file = MagicMock()
        mock_file.type = "image/jpeg"
        mock_file.name = "photo.jpg"
        url = svc.upload_image(mock_file, folder="targets")
        assert url is not None
        assert "test-bucket" in url
        assert url.endswith(".jpg") or "photo" in url

    def test_rejects_disallowed_file_type(self):
        svc = self._make_service()
        mock_file = MagicMock()
        mock_file.type = "application/pdf"
        mock_file.name = "doc.pdf"
        url = svc.upload_image(mock_file)
        assert url is None

    def test_returns_none_without_client(self):
        from services.s3_service import S3Service
        svc = MagicMock(spec=S3Service)
        svc.client = None
        svc.upload_image = S3Service.upload_image.__get__(svc)
        mock_file = MagicMock()
        mock_file.type = "image/png"
        assert svc.upload_image(mock_file) is None

    def test_path_traversal_safe(self):
        svc = self._make_service()
        mock_file = MagicMock()
        mock_file.type = "image/png"
        mock_file.name = "../../../etc/passwd"
        url = svc.upload_image(mock_file)
        assert url is not None
        assert "../" not in url
        assert "passwd" in url  # basename only

    @patch("services.s3_service.st")
    def test_upload_exception_returns_none(self, mock_st):
        svc = self._make_service()
        svc.client.upload_fileobj.side_effect = Exception("S3 error")
        mock_file = MagicMock()
        mock_file.type = "image/jpeg"
        mock_file.name = "test.jpg"
        url = svc.upload_image(mock_file)
        assert url is None


class TestDeleteImage:
    def _make_service(self):
        svc = MagicMock()
        svc.client = MagicMock()
        svc.bucket_name = "test-bucket"
        svc.region = "us-east-1"
        from services.s3_service import S3Service
        svc.delete_image = S3Service.delete_image.__get__(svc)
        return svc

    def test_delete_success(self):
        svc = self._make_service()
        url = "https://test-bucket.s3.us-east-1.amazonaws.com/targets/abc123_photo.jpg"
        result = svc.delete_image(url)
        assert result is True
        svc.client.delete_object.assert_called_once()

    def test_delete_returns_false_without_client(self):
        from services.s3_service import S3Service
        svc = MagicMock(spec=S3Service)
        svc.client = None
        svc.delete_image = S3Service.delete_image.__get__(svc)
        assert svc.delete_image("https://example.com/img.jpg") is False

    def test_delete_returns_false_for_none_url(self):
        svc = self._make_service()
        assert svc.delete_image(None) is False

    def test_delete_exception_returns_false(self):
        svc = self._make_service()
        svc.client.delete_object.side_effect = Exception("AWS error")
        result = svc.delete_image("https://test-bucket.s3.us-east-1.amazonaws.com/img.jpg")
        assert result is False
