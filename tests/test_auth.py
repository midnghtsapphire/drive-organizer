"""Tests for drive_organizer.auth module."""

import json
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from cryptography.fernet import Fernet

from drive_organizer.auth import (
    DriveAuthenticator,
    _get_or_create_key,
    _encrypt_data,
    _decrypt_data,
)


class TestEncryptionHelpers:
    """Test encryption helper functions."""

    def test_get_or_create_key_creates_new(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
            path = f.name
        os.unlink(path)  # Ensure it doesn't exist

        key = _get_or_create_key(path)
        assert isinstance(key, bytes)
        assert len(key) > 0
        # Verify it's a valid Fernet key
        Fernet(key)
        os.unlink(path)

    def test_get_or_create_key_reads_existing(self):
        key = Fernet.generate_key()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
            f.write(key)
            path = f.name

        result = _get_or_create_key(path)
        assert result == key
        os.unlink(path)

    def test_encrypt_decrypt_roundtrip(self):
        key = Fernet.generate_key()
        plaintext = "hello world secret data"
        encrypted = _encrypt_data(plaintext, key)
        decrypted = _decrypt_data(encrypted, key)
        assert decrypted == plaintext

    def test_encrypt_produces_different_output(self):
        key = Fernet.generate_key()
        plaintext = "test data"
        enc1 = _encrypt_data(plaintext, key)
        enc2 = _encrypt_data(plaintext, key)
        # Fernet uses random IV, so outputs differ
        assert enc1 != enc2

    def test_decrypt_wrong_key_fails(self):
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        encrypted = _encrypt_data("secret", key1)
        with pytest.raises(Exception):
            _decrypt_data(encrypted, key2)


class TestDriveAuthenticator:
    """Test DriveAuthenticator class."""

    def test_init_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            auth = DriveAuthenticator(
                credentials_file=os.path.join(tmpdir, "creds.json"),
                token_file=os.path.join(tmpdir, "token.json"),
                key_file=os.path.join(tmpdir, "test.key"),
            )
            assert auth.credentials_file.endswith("creds.json")
            assert auth.token_file.endswith("token.json")

    def test_load_token_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            auth = DriveAuthenticator(
                token_file=os.path.join(tmpdir, "nonexistent.json"),
                key_file=os.path.join(tmpdir, "test.key"),
            )
            result = auth._load_token()
            assert result is None

    def test_load_token_corrupted_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = os.path.join(tmpdir, "token.json")
            with open(token_path, "wb") as f:
                f.write(b"corrupted data not valid fernet")

            auth = DriveAuthenticator(
                token_file=token_path,
                key_file=os.path.join(tmpdir, "test.key"),
            )
            result = auth._load_token()
            assert result is None

    @patch("drive_organizer.auth.InstalledAppFlow")
    def test_run_auth_flow_no_credentials(self, mock_flow):
        with tempfile.TemporaryDirectory() as tmpdir:
            auth = DriveAuthenticator(
                credentials_file=os.path.join(tmpdir, "nonexistent.json"),
                key_file=os.path.join(tmpdir, "test.key"),
            )
            with pytest.raises(SystemExit):
                auth._run_auth_flow()

    def test_save_and_load_token(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            auth = DriveAuthenticator(
                token_file=os.path.join(tmpdir, "token.json"),
                key_file=os.path.join(tmpdir, "test.key"),
            )

            mock_creds = MagicMock()
            mock_creds.token = "access_token_123"
            mock_creds.refresh_token = "refresh_token_456"
            mock_creds.token_uri = "https://oauth2.googleapis.com/token"
            mock_creds.client_id = "client_id"
            mock_creds.client_secret = "client_secret"
            mock_creds.scopes = ["https://www.googleapis.com/auth/drive"]

            auth._save_token(mock_creds)

            # Verify file exists and is encrypted
            assert os.path.exists(os.path.join(tmpdir, "token.json"))
            with open(os.path.join(tmpdir, "token.json"), "rb") as f:
                content = f.read()
            # Should not be readable as plain JSON
            with pytest.raises(json.JSONDecodeError):
                json.loads(content)
