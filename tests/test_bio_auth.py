"""Tests for bio_auth module."""

import pytest
import json
import os
from unittest.mock import patch, MagicMock


class TestHashUsername:
    def test_deterministic(self):
        from bio_auth import _hash_username
        h1 = _hash_username("test_user")
        h2 = _hash_username("test_user")
        assert h1 == h2

    def test_different_users_different_hashes(self):
        from bio_auth import _hash_username
        h1 = _hash_username("user_a")
        h2 = _hash_username("user_b")
        assert h1 != h2

    def test_sha256_length(self):
        from bio_auth import _hash_username
        h = _hash_username("test")
        assert len(h) == 64


class TestEncryptDecrypt:
    @patch("core.models.get_encryption_suite")
    def test_encrypt_empty_returns_empty(self, mock_suite):
        from bio_auth import _encrypt
        assert _encrypt("") == ""
        assert _encrypt(None) == ""

    @patch("core.models.get_encryption_suite")
    def test_decrypt_empty_returns_empty(self, mock_suite):
        from bio_auth import _decrypt
        assert _decrypt("") == ""
        assert _decrypt(None) == ""

    @patch("core.models.get_encryption_suite")
    def test_encrypt_no_suite_returns_empty(self, mock_suite):
        mock_suite.return_value = None
        from bio_auth import _encrypt
        assert _encrypt("test") == ""

    @patch("core.models.get_encryption_suite")
    def test_decrypt_no_suite_returns_empty(self, mock_suite):
        mock_suite.return_value = None
        from bio_auth import _decrypt
        assert _decrypt("test") == ""

    @patch("core.models.get_encryption_suite")
    def test_encrypt_decrypt_roundtrip(self, mock_suite):
        suite = MagicMock()
        suite.encrypt.return_value = b"encrypted_data"
        suite.decrypt.return_value = b"original"
        mock_suite.return_value = suite

        from bio_auth import _encrypt, _decrypt
        encrypted = _encrypt("original")
        assert encrypted == "encrypted_data"

        decrypted = _decrypt(encrypted)
        assert decrypted == "original"

    @patch("core.models.get_encryption_suite")
    def test_decrypt_invalid_returns_empty(self, mock_suite):
        suite = MagicMock()
        suite.decrypt.side_effect = Exception("Invalid token")
        mock_suite.return_value = suite

        from bio_auth import _decrypt
        assert _decrypt("bad_data") == ""


class TestSaveAndCheckBiometrics:
    @patch("bio_auth._encrypt")
    @patch("bio_auth._hash_username")
    def test_save_creates_config(self, mock_hash, mock_encrypt, tmp_path):
        mock_encrypt.return_value = "enc_user"
        mock_hash.return_value = "hash_user"

        config_file = str(tmp_path / "device_config.json")
        with patch("bio_auth.CONFIG_FILE", config_file):
            from bio_auth import save_biometrics
            save_biometrics("test_user")

            assert os.path.exists(config_file)
            with open(config_file) as f:
                data = json.load(f)
            assert data["biometrics_enabled"] is True
            assert data["lp_secure"] == "enc_user"
            assert data["user_hash"] == "hash_user"

    def test_check_no_file_returns_none(self, tmp_path):
        config_file = str(tmp_path / "nonexistent.json")
        with patch("bio_auth.CONFIG_FILE", config_file):
            from bio_auth import check_biometrics_available
            assert check_biometrics_available() is None

    @patch("bio_auth._decrypt")
    @patch("bio_auth._hash_username")
    def test_check_valid_returns_username(self, mock_hash, mock_decrypt, tmp_path):
        mock_decrypt.return_value = "test_user"
        mock_hash.return_value = "correct_hash"

        config_file = str(tmp_path / "device_config.json")
        with open(config_file, "w") as f:
            json.dump({
                "lp_secure": "encrypted",
                "user_hash": "correct_hash",
                "biometrics_enabled": True,
            }, f)

        with patch("bio_auth.CONFIG_FILE", config_file):
            from bio_auth import check_biometrics_available
            assert check_biometrics_available() == "test_user"

    @patch("bio_auth._decrypt")
    @patch("bio_auth._hash_username")
    def test_check_hash_mismatch_returns_none(self, mock_hash, mock_decrypt, tmp_path):
        mock_decrypt.return_value = "test_user"
        mock_hash.return_value = "wrong_hash"

        config_file = str(tmp_path / "device_config.json")
        with open(config_file, "w") as f:
            json.dump({
                "lp_secure": "encrypted",
                "user_hash": "correct_hash",
                "biometrics_enabled": True,
            }, f)

        with patch("bio_auth.CONFIG_FILE", config_file):
            from bio_auth import check_biometrics_available
            assert check_biometrics_available() is None


class TestClearBiometrics:
    def test_clear_removes_file(self, tmp_path):
        config_file = str(tmp_path / "device_config.json")
        with open(config_file, "w") as f:
            f.write("{}")

        with patch("bio_auth.CONFIG_FILE", config_file):
            from bio_auth import clear_biometrics
            clear_biometrics()
            assert not os.path.exists(config_file)

    def test_clear_no_file_no_error(self, tmp_path):
        config_file = str(tmp_path / "nonexistent.json")
        with patch("bio_auth.CONFIG_FILE", config_file):
            from bio_auth import clear_biometrics
            clear_biometrics()
