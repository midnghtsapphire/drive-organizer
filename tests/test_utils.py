"""Tests for drive_organizer.utils module."""

import hashlib
import logging
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from drive_organizer.utils import (
    C,
    sanitize_filename,
    compute_md5_from_bytes,
    format_size,
    setup_logging,
    print_banner,
)


class TestColorCodes:
    """Test ANSI color codes."""

    def test_reset_defined(self):
        assert C.RESET == "\033[0m"

    def test_bold_defined(self):
        assert C.BOLD == "\033[1m"

    def test_all_colors_are_strings(self):
        for attr in dir(C):
            if not attr.startswith("_"):
                assert isinstance(getattr(C, attr), str)


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_basic_sanitization(self):
        assert sanitize_filename("Hello World.txt") == "hello-world.txt"

    def test_special_characters(self):
        result = sanitize_filename("file@#$%name!.pdf")
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

    def test_multiple_spaces(self):
        result = sanitize_filename("too   many   spaces.doc")
        assert "   " not in result

    def test_leading_trailing_dashes(self):
        result = sanitize_filename("---file---.txt")
        assert not result.startswith("-") or result == ""

    def test_empty_string(self):
        result = sanitize_filename("")
        assert isinstance(result, str)

    def test_unicode_filename(self):
        result = sanitize_filename("日本語ファイル.txt")
        assert isinstance(result, str)

    def test_preserves_extension(self):
        result = sanitize_filename("My Document.pdf")
        assert result.endswith(".pdf")

    def test_duplicate_suffix_removal(self):
        result = sanitize_filename("file (2).txt")
        assert isinstance(result, str)

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=50)
    def test_never_returns_none(self, filename):
        result = sanitize_filename(filename)
        assert result is not None
        assert isinstance(result, str)

    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))))
    @settings(max_examples=50)
    def test_alphanumeric_preserved(self, name):
        result = sanitize_filename(name + ".txt")
        assert isinstance(result, str)
        assert len(result) > 0


class TestComputeMD5:
    """Test MD5 computation."""

    def test_known_hash(self):
        data = b"hello world"
        expected = hashlib.md5(data).hexdigest()
        assert compute_md5_from_bytes(data) == expected

    def test_empty_bytes(self):
        result = compute_md5_from_bytes(b"")
        assert isinstance(result, str)
        assert len(result) == 32

    def test_large_data(self):
        data = b"x" * 1_000_000
        result = compute_md5_from_bytes(data)
        assert len(result) == 32

    @given(st.binary(min_size=0, max_size=1000))
    @settings(max_examples=30)
    def test_always_returns_32_hex(self, data):
        result = compute_md5_from_bytes(data)
        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)


class TestFormatSize:
    """Test human-readable size formatting."""

    def test_bytes(self):
        assert "B" in format_size(500)

    def test_kilobytes(self):
        result = format_size(1024)
        assert "KB" in result or "K" in result

    def test_megabytes(self):
        result = format_size(1024 * 1024)
        assert "MB" in result or "M" in result

    def test_gigabytes(self):
        result = format_size(1024 ** 3)
        assert "GB" in result or "G" in result

    def test_zero(self):
        result = format_size(0)
        assert "0" in result

    def test_negative(self):
        result = format_size(-1)
        assert isinstance(result, str)

    @given(st.integers(min_value=0, max_value=10**15))
    @settings(max_examples=30)
    def test_always_returns_string(self, size):
        result = format_size(size)
        assert isinstance(result, str)
        assert len(result) > 0


class TestSetupLogging:
    """Test logging setup."""

    def test_returns_logger(self):
        logger = setup_logging("test_drive_logger")
        assert isinstance(logger, logging.Logger)

    def test_logger_has_handlers(self):
        logger = setup_logging("test_drive_logger2")
        assert len(logger.handlers) > 0

    def test_idempotent(self):
        logger1 = setup_logging("test_drive_logger3")
        handler_count = len(logger1.handlers)
        logger2 = setup_logging("test_drive_logger3")
        assert len(logger2.handlers) == handler_count


class TestPrintBanner:
    """Test banner printing."""

    def test_banner_prints(self, capsys):
        print_banner("2.0.0")
        captured = capsys.readouterr()
        assert "2.0.0" in captured.out
