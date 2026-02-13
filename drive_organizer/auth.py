"""
Authentication Module for Drive Organizer v2
==============================================
OAuth2 handling with encrypted credential storage using Fernet.
Secure token handling with automatic refresh.
"""

from __future__ import annotations

import json
import os
import sys
import logging
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import SCOPES
from .utils import C


# ---------------------------------------------------------------------------
# Encryption Key Management
# ---------------------------------------------------------------------------
_KEY_FILE = ".drive_organizer_key"


def _get_or_create_key(key_path: Optional[str] = None) -> bytes:
    """Get or create a Fernet encryption key."""
    path = Path(key_path or _KEY_FILE)
    if path.exists():
        return path.read_bytes().strip()
    key = Fernet.generate_key()
    path.write_bytes(key)
    os.chmod(str(path), 0o600)
    return key


def _encrypt_data(data: str, key: bytes) -> bytes:
    """Encrypt string data with Fernet."""
    f = Fernet(key)
    return f.encrypt(data.encode("utf-8"))


def _decrypt_data(encrypted: bytes, key: bytes) -> str:
    """Decrypt Fernet-encrypted data."""
    f = Fernet(key)
    return f.decrypt(encrypted).decode("utf-8")


# ---------------------------------------------------------------------------
# Drive Authenticator
# ---------------------------------------------------------------------------
class DriveAuthenticator:
    """
    Handles OAuth2 authentication for Google Drive API.

    Features:
    - Encrypted token storage (Fernet symmetric encryption)
    - Automatic token refresh
    - Secure file permissions on token files
    """

    def __init__(
        self,
        credentials_file: str = "credentials.json",
        token_file: str = "token.json",
        key_file: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self._key = _get_or_create_key(key_file)
        self.logger = logger or logging.getLogger(__name__)

    def authenticate(self) -> Credentials:
        """
        Authenticate via OAuth2, opening browser on first run.
        Returns valid Credentials object.
        """
        creds = self._load_token()

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired token...")
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.warning(f"Token refresh failed: {e}")
                    creds = self._run_auth_flow()
            else:
                creds = self._run_auth_flow()
            self._save_token(creds)

        return creds

    def _load_token(self) -> Optional[Credentials]:
        """Load and decrypt stored token."""
        token_path = Path(self.token_file)
        if not token_path.exists():
            return None

        try:
            encrypted = token_path.read_bytes()
            token_json = _decrypt_data(encrypted, self._key)
            token_data = json.loads(token_json)
            return Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            self.logger.warning(f"Could not load encrypted token: {e}")
            # Try loading as plain JSON (migration from v1)
            try:
                with open(self.token_file, "r") as f:
                    token_data = json.load(f)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
                self.logger.info("Migrated plain token to encrypted storage")
                self._save_token(creds)
                return creds
            except Exception:
                return None

    def _save_token(self, creds: Credentials) -> None:
        """Encrypt and save token."""
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or SCOPES),
        }
        encrypted = _encrypt_data(json.dumps(token_data), self._key)
        token_path = Path(self.token_file)
        token_path.write_bytes(encrypted)
        os.chmod(str(token_path), 0o600)
        self.logger.debug("Token saved (encrypted)")

    def _run_auth_flow(self) -> Credentials:
        """Run the OAuth2 authorization flow."""
        if not os.path.exists(self.credentials_file):
            print(
                f"\n{C.RED}{C.BOLD}[FATAL]{C.RESET} "
                f"'{self.credentials_file}' not found!"
            )
            print(
                f"  Download it from Google Cloud Console → APIs & Services → Credentials"
            )
            sys.exit(1)

        self.logger.info("Starting OAuth2 authorization flow...")
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_file, SCOPES
        )
        creds = flow.run_local_server(port=0)
        self.logger.info("Authorization successful")
        return creds
