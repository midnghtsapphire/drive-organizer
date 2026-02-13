"""Tests for drive_organizer.config module."""

import json
import os
import tempfile
import pytest

from drive_organizer.config import (
    VERSION,
    APP_NAME,
    SCOPES,
    FOLDER_ARCHITECTURE,
    MUSIC_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    CODE_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    SPREADSHEET_EXTENSIONS,
    PRESENTATION_EXTENSIONS,
    STEM_EXTENSIONS,
    KEYWORD_RULES,
    GENRE_PATTERNS,
    RELEASE_STATUS_PATTERNS,
    MIME_FOLDER,
    DriveOrganizerConfig,
)


class TestConstants:
    """Test that all constants are properly defined."""

    def test_version_format(self):
        assert isinstance(VERSION, str)
        parts = VERSION.split(".")
        assert len(parts) == 3
        for p in parts:
            assert p.isdigit()

    def test_app_name(self):
        assert isinstance(APP_NAME, str)
        assert len(APP_NAME) > 0

    def test_scopes(self):
        assert isinstance(SCOPES, list)
        assert len(SCOPES) > 0
        assert all(s.startswith("https://") for s in SCOPES)

    def test_mime_folder(self):
        assert MIME_FOLDER == "application/vnd.google-apps.folder"

    def test_folder_architecture_is_dict(self):
        assert isinstance(FOLDER_ARCHITECTURE, dict)
        assert len(FOLDER_ARCHITECTURE) > 0

    def test_no_archive_folders(self):
        """CRITICAL: No archiving — all projects active."""
        def check_no_archive(d, path=""):
            for key, val in d.items():
                full = f"{path}/{key}" if path else key
                lower = key.lower()
                assert "archive" not in lower, f"Archive folder found: {full}"
                assert "old-project" not in lower, f"Old-Projects folder found: {full}"
                assert "completed" not in lower, f"Completed folder found: {full}"
                if isinstance(val, dict):
                    check_no_archive(val, full)
        check_no_archive(FOLDER_ARCHITECTURE)

    def test_all_projects_have_subfolders(self):
        """Every project under 02-PROJECTS should have detailed subfolders."""
        projects = FOLDER_ARCHITECTURE.get("02-PROJECTS", {})
        assert len(projects) > 0
        for proj_name, subfolders in projects.items():
            assert isinstance(subfolders, dict), f"Project {proj_name} has no subfolders"
            assert len(subfolders) >= 3, f"Project {proj_name} needs more subfolders"

    def test_music_extensions(self):
        assert ".mp3" in MUSIC_EXTENSIONS
        assert ".wav" in MUSIC_EXTENSIONS
        assert ".flac" in MUSIC_EXTENSIONS
        assert all(ext.startswith(".") for ext in MUSIC_EXTENSIONS)

    def test_image_extensions(self):
        assert ".jpg" in IMAGE_EXTENSIONS
        assert ".png" in IMAGE_EXTENSIONS
        assert all(ext.startswith(".") for ext in IMAGE_EXTENSIONS)

    def test_video_extensions(self):
        assert ".mp4" in VIDEO_EXTENSIONS
        assert all(ext.startswith(".") for ext in VIDEO_EXTENSIONS)

    def test_code_extensions(self):
        assert ".py" in CODE_EXTENSIONS
        assert ".js" in CODE_EXTENSIONS
        assert all(ext.startswith(".") for ext in CODE_EXTENSIONS)

    def test_document_extensions(self):
        assert ".pdf" in DOCUMENT_EXTENSIONS
        assert ".docx" in DOCUMENT_EXTENSIONS

    def test_keyword_rules_structure(self):
        assert isinstance(KEYWORD_RULES, list)
        for keywords, destination in KEYWORD_RULES:
            assert isinstance(keywords, list)
            assert isinstance(destination, str)
            assert len(keywords) > 0
            assert len(destination) > 0

    def test_genre_patterns(self):
        assert isinstance(GENRE_PATTERNS, dict)
        assert len(GENRE_PATTERNS) > 0
        for genre, keywords in GENRE_PATTERNS.items():
            assert isinstance(keywords, list)
            assert len(keywords) > 0

    def test_release_status_patterns(self):
        assert isinstance(RELEASE_STATUS_PATTERNS, dict)
        assert "Released" in RELEASE_STATUS_PATTERNS
        assert "Unreleased" in RELEASE_STATUS_PATTERNS
        assert "Work-In-Progress" in RELEASE_STATUS_PATTERNS


class TestDriveOrganizerConfig:
    """Test DriveOrganizerConfig dataclass."""

    def test_default_values(self):
        config = DriveOrganizerConfig()
        assert config.api_calls_per_second == 8
        assert config.batch_size == 100
        assert config.max_retries == 7
        assert config.base_delay == 1.0
        assert config.dry_run is True
        assert config.verbose is False

    def test_custom_values(self):
        config = DriveOrganizerConfig(
            api_calls_per_second=5,
            batch_size=50,
            max_retries=3,
            dry_run=False,
        )
        assert config.api_calls_per_second == 5
        assert config.batch_size == 50
        assert config.max_retries == 3
        assert config.dry_run is False

    def test_from_json(self):
        data = {
            "api_calls_per_second": 12,
            "batch_size": 200,
            "max_retries": 5,
            "dry_run": False,
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            config = DriveOrganizerConfig.from_json(f.name)

        assert config.api_calls_per_second == 12
        assert config.batch_size == 200
        assert config.max_retries == 5
        assert config.dry_run is False
        os.unlink(f.name)

    def test_from_json_ignores_unknown_keys(self):
        data = {"api_calls_per_second": 5, "unknown_key": "value"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            config = DriveOrganizerConfig.from_json(f.name)

        assert config.api_calls_per_second == 5
        os.unlink(f.name)

    def test_to_json(self):
        config = DriveOrganizerConfig(api_calls_per_second=15)
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as f:
            config.to_json(f.name)
            with open(f.name) as rf:
                data = json.load(rf)

        assert data["api_calls_per_second"] == 15
        os.unlink(f.name)
