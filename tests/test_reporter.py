"""Tests for drive_organizer.reporter module."""

import json
import os
import tempfile
import pytest

from drive_organizer.categorizer import DriveFile, MigrationAction, ScanReport
from drive_organizer.reporter import ReportGenerator


class TestReportGenerator:
    """Test ReportGenerator."""

    def setup_method(self):
        self.reporter = ReportGenerator()

    def test_generate_scan_report(self):
        files = {
            "1": DriveFile(id="1", name="song.mp3", mime_type="audio/mpeg", size=5000),
            "2": DriveFile(id="2", name="doc.pdf", mime_type="application/pdf", size=3000),
        }
        report = self.reporter.generate_scan_report(files, {})
        assert report.total_files == 2
        assert report.total_size_bytes == 8000

    def test_generate_scan_report_empty(self):
        report = self.reporter.generate_scan_report({}, {})
        assert report.total_files == 0
        assert report.total_size_bytes == 0

    def test_print_scan_report(self, capsys):
        report = ScanReport(
            total_files=100,
            total_folders=20,
            total_size_bytes=1024 * 1024,
            file_type_counts={".mp3": 50, ".pdf": 30, ".py": 20},
            music_files=50,
            document_files=30,
        )
        self.reporter.print_scan_report(report)
        captured = capsys.readouterr()
        assert "100" in captured.out
        assert "SCAN REPORT" in captured.out

    def test_print_migration_summary(self, capsys):
        actions = [
            MigrationAction(action_type="move", file_id="1", file_name="test.txt"),
        ]
        stats = {"total_planned": 1, "executed": 1, "skipped": 0, "errors": 0}
        self.reporter.print_migration_summary(actions, stats)
        captured = capsys.readouterr()
        assert "MIGRATION SUMMARY" in captured.out

    def test_export_json(self):
        report = ScanReport(total_files=10)
        actions = []
        stats = {"total_planned": 0}

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            self.reporter.export_json(report, actions, stats, f.name)
            with open(f.name) as rf:
                data = json.load(rf)
            assert "timestamp" in data
            assert "scan_report" in data
        os.unlink(f.name)

    def test_export_markdown(self):
        report = ScanReport(total_files=10, file_type_counts={".mp3": 5})
        actions = []
        stats = {"total_planned": 0}

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            self.reporter.export_markdown(report, actions, stats, f.name)
            with open(f.name) as rf:
                content = rf.read()
            assert "Drive Organizer Report" in content
            assert "10" in content
        os.unlink(f.name)

    def test_print_dry_run_notice(self, capsys):
        stats = {"total_planned": 5, "executed": 0, "skipped": 5, "errors": 0, "dry_run": True}
        self.reporter.print_migration_summary([], stats)
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
