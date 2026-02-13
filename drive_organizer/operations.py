"""
API Operations Module for Drive Organizer v2
==============================================
Google Drive API operations with token bucket rate limiter
and exponential backoff retry logic.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from .config import MIME_FOLDER, DriveOrganizerConfig
from .utils import C


# ---------------------------------------------------------------------------
# Token Bucket Rate Limiter
# ---------------------------------------------------------------------------
class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for API calls.

    Allows bursts up to `capacity` tokens, refilling at `rate` tokens/second.
    Thread-safe implementation.
    """

    def __init__(self, rate: float = 8.0, capacity: float = 10.0):
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> float:
        """
        Acquire tokens, blocking if necessary.
        Returns the time waited (seconds).
        """
        waited = 0.0
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return waited
                # Calculate wait time
                deficit = tokens - self._tokens
                wait_time = deficit / self.rate
            time.sleep(wait_time)
            waited += wait_time

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    @property
    def available_tokens(self) -> float:
        """Current number of available tokens."""
        with self._lock:
            self._refill()
            return self._tokens


# ---------------------------------------------------------------------------
# API Call with Exponential Backoff
# ---------------------------------------------------------------------------
def api_call_with_backoff(
    func: Callable,
    *args: Any,
    max_retries: int = 7,
    base_delay: float = 1.0,
    rate_limiter: Optional[TokenBucketRateLimiter] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any,
) -> Any:
    """
    Execute an API call with exponential backoff on rate-limit errors.

    Integrates with TokenBucketRateLimiter for proactive rate limiting.
    Retries on HTTP 429, 500, 503 errors.
    """
    _logger = logger or logging.getLogger(__name__)

    if rate_limiter:
        rate_limiter.acquire()

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except HttpError as e:
            status = e.resp.status if hasattr(e, "resp") else 0
            if status in (429, 500, 503):
                delay = base_delay * (2 ** attempt)
                _logger.warning(
                    f"API error (HTTP {status}). "
                    f"Retry {attempt + 1}/{max_retries} in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                raise
        except ConnectionError as e:
            delay = base_delay * (2 ** attempt)
            _logger.warning(
                f"Connection error: {e}. "
                f"Retry {attempt + 1}/{max_retries} in {delay:.1f}s..."
            )
            time.sleep(delay)

    raise RuntimeError(f"API call failed after {max_retries} retries")


# ---------------------------------------------------------------------------
# Drive API Operations
# ---------------------------------------------------------------------------
class DriveOperations:
    """
    Encapsulates Google Drive API operations with rate limiting.
    """

    def __init__(
        self,
        credentials: Credentials,
        config: Optional[DriveOrganizerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config or DriveOrganizerConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.service = build("drive", "v3", credentials=credentials)
        self.rate_limiter = TokenBucketRateLimiter(
            rate=self.config.api_calls_per_second,
            capacity=self.config.api_calls_per_second + 2,
        )

    def _call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Wrapper for rate-limited API calls with backoff."""
        return api_call_with_backoff(
            func,
            *args,
            max_retries=self.config.max_retries,
            base_delay=self.config.base_delay,
            rate_limiter=self.rate_limiter,
            logger=self.logger,
            **kwargs,
        )

    def list_all_files(
        self,
        page_size: int = 100,
        fields: str = (
            "nextPageToken, files(id, name, mimeType, size, md5Checksum, "
            "parents, createdTime, modifiedTime, trashed)"
        ),
    ) -> List[Dict[str, Any]]:
        """List all files in Drive (non-trashed)."""
        all_files: List[Dict[str, Any]] = []
        page_token = None

        while True:
            kwargs: Dict[str, Any] = {
                "pageSize": page_size,
                "fields": fields,
                "q": "trashed = false",
            }
            if page_token:
                kwargs["pageToken"] = page_token

            result = self._call(
                self.service.files().list(**kwargs).execute
            )
            files = result.get("files", [])
            all_files.extend(files)

            self.logger.debug(f"Fetched {len(files)} files (total: {len(all_files)})")

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return all_files

    def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
    ) -> str:
        """Create a folder and return its ID."""
        metadata: Dict[str, Any] = {
            "name": name,
            "mimeType": MIME_FOLDER,
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        result = self._call(
            self.service.files().create(
                body=metadata, fields="id"
            ).execute
        )
        folder_id = result["id"]
        self.logger.debug(f"Created folder: {name} ({folder_id})")
        return folder_id

    def move_file(
        self,
        file_id: str,
        new_parent_id: str,
        old_parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Move a file to a new parent folder."""
        remove_parents = old_parent_id or ""
        result = self._call(
            self.service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=remove_parents,
                fields="id, parents",
            ).execute
        )
        return result

    def rename_file(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a file."""
        result = self._call(
            self.service.files().update(
                fileId=file_id,
                body={"name": new_name},
                fields="id, name",
            ).execute
        )
        return result

    def get_file_metadata(
        self,
        file_id: str,
        fields: str = "id, name, mimeType, size, parents, md5Checksum",
    ) -> Dict[str, Any]:
        """Get metadata for a single file."""
        return self._call(
            self.service.files().get(
                fileId=file_id, fields=fields
            ).execute
        )

    def find_folder_by_name(
        self,
        name: str,
        parent_id: Optional[str] = None,
    ) -> Optional[str]:
        """Find a folder by name, optionally within a parent. Returns ID or None."""
        q = f"mimeType = '{MIME_FOLDER}' and name = '{name}' and trashed = false"
        if parent_id:
            q += f" and '{parent_id}' in parents"

        result = self._call(
            self.service.files().list(
                q=q, fields="files(id, name)", pageSize=1
            ).execute
        )
        files = result.get("files", [])
        return files[0]["id"] if files else None

    def ensure_folder_path(
        self,
        path: str,
        root_id: Optional[str] = None,
    ) -> str:
        """
        Ensure a full folder path exists, creating folders as needed.
        Returns the ID of the deepest folder.
        """
        parts = [p for p in path.split("/") if p]
        current_parent = root_id

        for part in parts:
            existing = self.find_folder_by_name(part, current_parent)
            if existing:
                current_parent = existing
            else:
                current_parent = self.create_folder(part, current_parent)

        return current_parent
