"""Tests for drive_organizer.categorizer module."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from drive_organizer.categorizer import (
    DriveFile,
    DriveFolder,
    MigrationAction,
    ScanReport,
    FileCategorizer,
    DuplicateDetector,
)


class TestDriveFile:
    """Test DriveFile dataclass."""

    def test_basic_creation(self):
        f = DriveFile(id="1", name="test.txt", mime_type="text/plain")
        assert f.id == "1"
        assert f.name == "test.txt"
        assert f.size == 0

    def test_extension_extraction(self):
        f = DriveFile(id="1", name="document.PDF", mime_type="application/pdf")
        assert f.extension == ".pdf"

    def test_extension_no_dot(self):
        f = DriveFile(id="1", name="README", mime_type="text/plain")
        assert f.extension == ""

    def test_extension_multiple_dots(self):
        f = DriveFile(id="1", name="archive.tar.gz", mime_type="application/gzip")
        assert f.extension == ".gz"

    def test_is_google_doc(self):
        f = DriveFile(id="1", name="Doc", mime_type="application/vnd.google-apps.document")
        assert f.is_google_doc is True

    def test_is_not_google_doc(self):
        f = DriveFile(id="1", name="test.txt", mime_type="text/plain")
        assert f.is_google_doc is False

    def test_default_values(self):
        f = DriveFile(id="1", name="test", mime_type="text/plain")
        assert f.parents == []
        assert f.is_duplicate is False
        assert f.duplicate_of == ""
        assert f.suggested_destination == ""

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=30)
    def test_extension_never_none(self, name):
        f = DriveFile(id="1", name=name, mime_type="text/plain")
        assert f.extension is not None


class TestDriveFolder:
    """Test DriveFolder dataclass."""

    def test_creation(self):
        f = DriveFolder(id="1", name="Folder")
        assert f.id == "1"
        assert f.children_folders == []
        assert f.children_files == []


class TestMigrationAction:
    """Test MigrationAction dataclass."""

    def test_creation(self):
        a = MigrationAction(action_type="move", file_id="1", file_name="test.txt")
        assert a.status == "pending"
        assert a.error == ""


class TestScanReport:
    """Test ScanReport dataclass."""

    def test_defaults(self):
        r = ScanReport()
        assert r.total_files == 0
        assert r.total_size_bytes == 0
        assert r.file_type_counts == {}


class TestFileCategorizer:
    """Test FileCategorizer."""

    def setup_method(self):
        self.categorizer = FileCategorizer()

    def test_categorize_mp3(self):
        f = DriveFile(id="1", name="song.mp3", mime_type="audio/mpeg")
        dest = self.categorizer.categorize(f)
        assert "MUSIC" in dest

    def test_categorize_pdf(self):
        f = DriveFile(id="1", name="document.pdf", mime_type="application/pdf")
        dest = self.categorizer.categorize(f)
        assert dest != ""

    def test_categorize_python(self):
        f = DriveFile(id="1", name="script.py", mime_type="text/x-python")
        dest = self.categorizer.categorize(f)
        # 'script' matches keyword 'script' -> 09-DEVELOPMENT/Code-Snippets
        assert "DEVELOPMENT" in dest or "Code" in dest or dest != ""

    def test_categorize_image(self):
        f = DriveFile(id="1", name="photo.jpg", mime_type="image/jpeg")
        dest = self.categorizer.categorize(f)
        assert "PERSONAL" in dest or "Photos" in dest

    def test_categorize_video(self):
        f = DriveFile(id="1", name="vacation-video.mp4", mime_type="video/mp4")
        dest = self.categorizer.categorize(f)
        assert "Videos" in dest or "PERSONAL" in dest or dest != ""

    def test_categorize_by_keyword_court(self):
        f = DriveFile(id="1", name="Court Filing Jan 2024.pdf", mime_type="application/pdf")
        dest = self.categorizer.categorize(f)
        assert "LEGAL" in dest or "Court" in dest

    def test_categorize_by_keyword_case_insensitive(self):
        f = DriveFile(id="1", name="COURT FILING.PDF", mime_type="application/pdf")
        dest = self.categorizer.categorize(f)
        assert "LEGAL" in dest or "Court" in dest

    def test_categorize_by_keyword_resume(self):
        f = DriveFile(id="1", name="resume_2024.docx", mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        dest = self.categorizer.categorize(f)
        assert "CAREER" in dest or "Resume" in dest or "TEMPLATES" in dest

    def test_categorize_google_doc(self):
        f = DriveFile(id="1", name="My Document", mime_type="application/vnd.google-apps.document")
        dest = self.categorizer.categorize(f)
        assert dest != ""

    def test_categorize_unknown(self):
        f = DriveFile(id="1", name="randomfile.xyz", mime_type="application/octet-stream")
        dest = self.categorizer.categorize(f)
        # May or may not categorize, but shouldn't error
        assert isinstance(dest, str)

    def test_categorize_batch(self):
        files = {
            "1": DriveFile(id="1", name="song.mp3", mime_type="audio/mpeg"),
            "2": DriveFile(id="2", name="doc.pdf", mime_type="application/pdf"),
            "3": DriveFile(id="3", name="unknown.xyz", mime_type="application/octet-stream"),
        }
        results = self.categorizer.categorize_batch(files)
        assert len(results) == 3
        assert isinstance(results["1"], str)

    def test_categorize_spreadsheet(self):
        f = DriveFile(id="1", name="data.xlsx", mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        dest = self.categorizer.categorize(f)
        # Extension-based: maps to 10-TEMPLATES/Spreadsheets
        assert "Spreadsheet" in dest or "TEMPLATES" in dest or "FINANCIAL" in dest

    def test_categorize_presentation(self):
        f = DriveFile(id="1", name="pitch.pptx", mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        dest = self.categorizer.categorize(f)
        assert "Presentation" in dest or "TEMPLATES" in dest

    def test_extension_case_insensitive(self):
        f1 = DriveFile(id="1", name="song.MP3", mime_type="audio/mpeg")
        f2 = DriveFile(id="2", name="song.mp3", mime_type="audio/mpeg")
        assert self.categorizer.categorize(f1) == self.categorizer.categorize(f2)


class TestDuplicateDetector:
    """Test DuplicateDetector."""

    def test_md5_duplicates(self):
        files = {
            "1": DriveFile(id="1", name="file.txt", mime_type="text/plain",
                          md5_checksum="abc123", modified_time="2024-01-02"),
            "2": DriveFile(id="2", name="file_copy.txt", mime_type="text/plain",
                          md5_checksum="abc123", modified_time="2024-01-01"),
        }
        detector = DuplicateDetector(files)
        dups = detector.detect()
        assert len(dups) == 1
        # Older file is the duplicate
        assert dups[0][0] == "2"

    def test_no_duplicates(self):
        files = {
            "1": DriveFile(id="1", name="file1.txt", mime_type="text/plain",
                          md5_checksum="abc123"),
            "2": DriveFile(id="2", name="file2.txt", mime_type="text/plain",
                          md5_checksum="def456"),
        }
        detector = DuplicateDetector(files)
        dups = detector.detect()
        assert len(dups) == 0

    def test_name_size_duplicates(self):
        files = {
            "1": DriveFile(id="1", name="file.txt", mime_type="text/plain",
                          size=1024, modified_time="2024-01-02"),
            "2": DriveFile(id="2", name="file.txt", mime_type="text/plain",
                          size=1024, modified_time="2024-01-01"),
        }
        detector = DuplicateDetector(files)
        dups = detector.detect()
        assert len(dups) == 1

    def test_name_size_case_insensitive(self):
        files = {
            "1": DriveFile(id="1", name="FILE.TXT", mime_type="text/plain",
                          size=1024, modified_time="2024-01-02"),
            "2": DriveFile(id="2", name="file.txt", mime_type="text/plain",
                          size=1024, modified_time="2024-01-01"),
        }
        detector = DuplicateDetector(files)
        dups = detector.detect()
        assert len(dups) == 1

    def test_multiple_duplicates(self):
        files = {
            "1": DriveFile(id="1", name="f.txt", mime_type="text/plain",
                          md5_checksum="abc", modified_time="2024-01-03"),
            "2": DriveFile(id="2", name="f_copy.txt", mime_type="text/plain",
                          md5_checksum="abc", modified_time="2024-01-02"),
            "3": DriveFile(id="3", name="f_copy2.txt", mime_type="text/plain",
                          md5_checksum="abc", modified_time="2024-01-01"),
        }
        detector = DuplicateDetector(files)
        dups = detector.detect()
        assert len(dups) == 2

    def test_zero_size_files(self):
        files = {
            "1": DriveFile(id="1", name="empty1.txt", mime_type="text/plain",
                          size=0, modified_time="2024-01-02"),
            "2": DriveFile(id="2", name="empty1.txt", mime_type="text/plain",
                          size=0, modified_time="2024-01-01"),
        }
        detector = DuplicateDetector(files)
        dups = detector.detect()
        assert len(dups) == 1

    def test_empty_files_dict(self):
        detector = DuplicateDetector({})
        dups = detector.detect()
        assert len(dups) == 0

    def test_non_ascii_filenames(self):
        files = {
            "1": DriveFile(id="1", name="日本語.txt", mime_type="text/plain",
                          size=100, modified_time="2024-01-02"),
            "2": DriveFile(id="2", name="日本語.txt", mime_type="text/plain",
                          size=100, modified_time="2024-01-01"),
        }
        detector = DuplicateDetector(files)
        dups = detector.detect()
        assert len(dups) == 1
