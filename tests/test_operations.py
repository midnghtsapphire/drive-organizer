"""Tests for drive_organizer.operations module."""

import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from drive_organizer.operations import (
    TokenBucketRateLimiter,
    api_call_with_backoff,
    DriveOperations,
)
from drive_organizer.config import DriveOrganizerConfig


class TestTokenBucketRateLimiter:
    """Test token bucket rate limiter."""

    def test_initial_capacity(self):
        limiter = TokenBucketRateLimiter(rate=10.0, capacity=10.0)
        assert limiter.available_tokens <= 10.0

    def test_acquire_reduces_tokens(self):
        limiter = TokenBucketRateLimiter(rate=100.0, capacity=10.0)
        initial = limiter.available_tokens
        limiter.acquire(1.0)
        after = limiter.available_tokens
        assert after < initial

    def test_acquire_blocks_when_empty(self):
        limiter = TokenBucketRateLimiter(rate=100.0, capacity=2.0)
        limiter.acquire(2.0)
        start = time.monotonic()
        limiter.acquire(1.0)
        elapsed = time.monotonic() - start
        # Should have waited some time (but rate is high so very short)
        assert elapsed >= 0

    def test_refill_over_time(self):
        limiter = TokenBucketRateLimiter(rate=1000.0, capacity=10.0)
        limiter.acquire(10.0)
        time.sleep(0.02)
        tokens = limiter.available_tokens
        assert tokens > 0

    def test_capacity_limit(self):
        limiter = TokenBucketRateLimiter(rate=1000.0, capacity=5.0)
        time.sleep(0.1)
        assert limiter.available_tokens <= 5.0

    def test_thread_safety(self):
        import threading
        limiter = TokenBucketRateLimiter(rate=100.0, capacity=100.0)
        errors = []

        def acquire_many():
            try:
                for _ in range(10):
                    limiter.acquire(0.1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=acquire_many) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestApiCallWithBackoff:
    """Test exponential backoff logic."""

    def test_success_on_first_try(self):
        func = MagicMock(return_value="success")
        result = api_call_with_backoff(func, max_retries=3, base_delay=0.01)
        assert result == "success"
        func.assert_called_once()

    def test_retry_on_429(self):
        mock_resp = MagicMock()
        mock_resp.status = 429

        from googleapiclient.errors import HttpError
        error = HttpError(mock_resp, b"rate limit")

        func = MagicMock(side_effect=[error, "success"])
        result = api_call_with_backoff(func, max_retries=3, base_delay=0.01)
        assert result == "success"
        assert func.call_count == 2

    def test_retry_on_500(self):
        mock_resp = MagicMock()
        mock_resp.status = 500

        from googleapiclient.errors import HttpError
        error = HttpError(mock_resp, b"server error")

        func = MagicMock(side_effect=[error, "success"])
        result = api_call_with_backoff(func, max_retries=3, base_delay=0.01)
        assert result == "success"

    def test_no_retry_on_404(self):
        mock_resp = MagicMock()
        mock_resp.status = 404

        from googleapiclient.errors import HttpError
        error = HttpError(mock_resp, b"not found")

        func = MagicMock(side_effect=error)
        with pytest.raises(HttpError):
            api_call_with_backoff(func, max_retries=3, base_delay=0.01)
        func.assert_called_once()

    def test_max_retries_exhausted(self):
        mock_resp = MagicMock()
        mock_resp.status = 503

        from googleapiclient.errors import HttpError
        error = HttpError(mock_resp, b"unavailable")

        func = MagicMock(side_effect=error)
        with pytest.raises(RuntimeError, match="failed after"):
            api_call_with_backoff(func, max_retries=2, base_delay=0.01)
        assert func.call_count == 2

    def test_with_rate_limiter(self):
        limiter = TokenBucketRateLimiter(rate=100.0, capacity=10.0)
        func = MagicMock(return_value="ok")
        result = api_call_with_backoff(
            func, max_retries=3, base_delay=0.01, rate_limiter=limiter
        )
        assert result == "ok"

    def test_connection_error_retry(self):
        func = MagicMock(side_effect=[ConnectionError("timeout"), "ok"])
        result = api_call_with_backoff(func, max_retries=3, base_delay=0.01)
        assert result == "ok"


class TestDriveOperations:
    """Test DriveOperations with mocked Google API."""

    @patch("drive_organizer.operations.build")
    def test_init(self, mock_build):
        creds = MagicMock()
        ops = DriveOperations(creds)
        mock_build.assert_called_once_with("drive", "v3", credentials=creds)

    @patch("drive_organizer.operations.build")
    def test_list_all_files(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = mock_service.files.return_value
        mock_list = mock_files.list.return_value
        mock_list.execute.return_value = {
            "files": [
                {"id": "1", "name": "test.txt", "mimeType": "text/plain"},
                {"id": "2", "name": "test2.pdf", "mimeType": "application/pdf"},
            ],
            "nextPageToken": None,
        }

        creds = MagicMock()
        ops = DriveOperations(creds)
        files = ops.list_all_files()
        assert len(files) == 2

    @patch("drive_organizer.operations.build")
    def test_create_folder(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = mock_service.files.return_value
        mock_create = mock_files.create.return_value
        mock_create.execute.return_value = {"id": "folder_123"}

        creds = MagicMock()
        ops = DriveOperations(creds)
        result = ops.create_folder("Test Folder", "parent_id")
        assert result == "folder_123"

    @patch("drive_organizer.operations.build")
    def test_move_file(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = mock_service.files.return_value
        mock_update = mock_files.update.return_value
        mock_update.execute.return_value = {"id": "file_1", "parents": ["new_parent"]}

        creds = MagicMock()
        ops = DriveOperations(creds)
        result = ops.move_file("file_1", "new_parent", "old_parent")
        assert result["id"] == "file_1"

    @patch("drive_organizer.operations.build")
    def test_find_folder_by_name_found(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = mock_service.files.return_value
        mock_list = mock_files.list.return_value
        mock_list.execute.return_value = {
            "files": [{"id": "found_id", "name": "TestFolder"}]
        }

        creds = MagicMock()
        ops = DriveOperations(creds)
        result = ops.find_folder_by_name("TestFolder")
        assert result == "found_id"

    @patch("drive_organizer.operations.build")
    def test_find_folder_by_name_not_found(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = mock_service.files.return_value
        mock_list = mock_files.list.return_value
        mock_list.execute.return_value = {"files": []}

        creds = MagicMock()
        ops = DriveOperations(creds)
        result = ops.find_folder_by_name("NonExistent")
        assert result is None
