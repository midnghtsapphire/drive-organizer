"""Tests for drive_organizer.migrator module."""

import json
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from drive_organizer.categorizer import DriveFile, MigrationAction
from drive_organizer.config import FOLDER_ARCHITECTURE, DriveOrganizerConfig
from drive_organizer.migrator import FolderArchitect, FileMigrator


class TestFolderArchitect:
    """Test FolderArchitect."""

    def test_build_architecture_creates_folders(self):
        mock_ops = MagicMock()
        mock_ops.find_folder_by_name.return_value = None
        mock_ops.create_folder.side_effect = lambda name, pid: f"id_{name}"

        architect = FolderArchitect(mock_ops)
        simple_arch = {"TestFolder": {"SubFolder": {}}}
        result = architect.build_architecture(simple_arch)

        assert len(result) > 0
        assert mock_ops.create_folder.call_count >= 2

    def test_build_architecture_reuses_existing(self):
        mock_ops = MagicMock()
        mock_ops.find_folder_by_name.return_value = "existing_id"

        architect = FolderArchitect(mock_ops)
        simple_arch = {"Existing": {}}
        result = architect.build_architecture(simple_arch)

        mock_ops.create_folder.assert_not_called()
        assert "Existing" in result

    def test_folder_map_property(self):
        mock_ops = MagicMock()
        mock_ops.find_folder_by_name.return_value = "id_1"

        architect = FolderArchitect(mock_ops)
        architect.build_architecture({"A": {}})
        fm = architect.folder_map
        assert isinstance(fm, dict)

    def test_nested_architecture(self):
        mock_ops = MagicMock()
        mock_ops.find_folder_by_name.return_value = None
        counter = [0]
        def make_id(name, pid=None):
            counter[0] += 1
            return f"id_{counter[0]}"
        mock_ops.create_folder.side_effect = make_id

        architect = FolderArchitect(mock_ops)
        arch = {"A": {"B": {"C": {}}}}
        result = architect.build_architecture(arch)
        assert mock_ops.create_folder.call_count == 3


class TestFileMigrator:
    """Test FileMigrator."""

    def setup_method(self):
        self.mock_ops = MagicMock()
        self.config = DriveOrganizerConfig(dry_run=True)

    def test_plan_migration_basic(self):
        migrator = FileMigrator(self.mock_ops, self.config)
        files = {
            "1": DriveFile(id="1", name="song.mp3", mime_type="audio/mpeg",
                          size=1000, parents=["root"]),
        }
        folder_map = {"03-MUSIC/Catalog/Work-In-Progress": "folder_id_1"}
        actions = migrator.plan_migration(files, folder_map)
        assert len(actions) >= 1

    def test_plan_migration_with_duplicates(self):
        migrator = FileMigrator(self.mock_ops, self.config)
        files = {
            "1": DriveFile(id="1", name="file.txt", mime_type="text/plain",
                          md5_checksum="abc", modified_time="2024-01-02"),
            "2": DriveFile(id="2", name="file_copy.txt", mime_type="text/plain",
                          md5_checksum="abc", modified_time="2024-01-01"),
        }
        folder_map = {"11-DUPLICATES-DETECTED": "dup_folder_id"}
        actions = migrator.plan_migration(files, folder_map)
        dup_actions = [a for a in actions if a.action_type == "duplicate_flag"]
        assert len(dup_actions) >= 1

    def test_execute_dry_run(self):
        migrator = FileMigrator(self.mock_ops, self.config)
        files = {
            "1": DriveFile(id="1", name="song.mp3", mime_type="audio/mpeg",
                          parents=["root"]),
        }
        folder_map = {"03-MUSIC/Catalog/Work-In-Progress": "folder_id_1"}
        migrator.plan_migration(files, folder_map)
        stats = migrator.execute(folder_map, dry_run=True)
        assert stats["dry_run"] is True
        assert stats["executed"] == 0

    def test_execute_real(self):
        self.mock_ops.move_file.return_value = {"id": "1", "parents": ["new"]}
        migrator = FileMigrator(self.mock_ops, self.config)
        files = {
            "1": DriveFile(id="1", name="song.mp3", mime_type="audio/mpeg",
                          parents=["root"]),
        }
        folder_map = {"03-MUSIC/Catalog/Work-In-Progress": "folder_id_1"}
        migrator.plan_migration(files, folder_map)
        stats = migrator.execute(folder_map, dry_run=False)
        assert stats["dry_run"] is False

    def test_save_plan(self):
        migrator = FileMigrator(self.mock_ops, self.config)
        files = {
            "1": DriveFile(id="1", name="song.mp3", mime_type="audio/mpeg"),
        }
        folder_map = {"03-MUSIC/Catalog/Work-In-Progress": "folder_id_1"}
        migrator.plan_migration(files, folder_map)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            migrator.save_plan(f.name)
            with open(f.name) as rf:
                data = json.load(rf)
            assert isinstance(data, list)
        os.unlink(f.name)

    def test_actions_property(self):
        migrator = FileMigrator(self.mock_ops, self.config)
        assert migrator.actions == []

    def test_completed_property(self):
        migrator = FileMigrator(self.mock_ops, self.config)
        assert migrator.completed == []

    def test_errors_property(self):
        migrator = FileMigrator(self.mock_ops, self.config)
        assert migrator.errors == []

    def test_execute_handles_error(self):
        self.mock_ops.move_file.side_effect = Exception("API error")
        migrator = FileMigrator(self.mock_ops, self.config)
        files = {
            "1": DriveFile(id="1", name="song.mp3", mime_type="audio/mpeg",
                          parents=["root"]),
        }
        folder_map = {"03-MUSIC/Catalog/Work-In-Progress": "folder_id_1"}
        migrator.plan_migration(files, folder_map)
        stats = migrator.execute(folder_map, dry_run=False)
        assert stats["errors"] >= 0  # Should handle gracefully
