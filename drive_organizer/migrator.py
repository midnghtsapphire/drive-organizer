"""
File Migration Module for Drive Organizer v2
==============================================
Handles file migration planning, execution, and rollback.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .categorizer import DriveFile, DuplicateDetector, FileCategorizer, MigrationAction
from .config import DriveOrganizerConfig, FOLDER_ARCHITECTURE
from .music_organizer import MusicOrganizer
from .operations import DriveOperations
from .utils import C, sanitize_filename


# ---------------------------------------------------------------------------
# Folder Architect
# ---------------------------------------------------------------------------
class FolderArchitect:
    """
    Creates the folder architecture in Google Drive.
    Recursively builds the hierarchy defined in config.
    """

    def __init__(
        self,
        ops: DriveOperations,
        logger: Optional[logging.Logger] = None,
    ):
        self.ops = ops
        self.logger = logger or logging.getLogger(__name__)
        self._folder_cache: Dict[str, str] = {}  # path → folder_id

    def build_architecture(
        self,
        architecture: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
        prefix: str = "",
    ) -> Dict[str, str]:
        """
        Recursively create the folder architecture.
        Returns a mapping of folder_path → folder_id.
        """
        arch = architecture or FOLDER_ARCHITECTURE

        for name, children in arch.items():
            path = f"{prefix}{name}" if not prefix else f"{prefix}/{name}"

            # Check cache first
            if path in self._folder_cache:
                folder_id = self._folder_cache[path]
            else:
                # Check if folder exists
                existing = self.ops.find_folder_by_name(name, parent_id)
                if existing:
                    folder_id = existing
                    self.logger.debug(f"Folder exists: {path}")
                else:
                    folder_id = self.ops.create_folder(name, parent_id)
                    self.logger.info(f"{C.GREEN}Created:{C.RESET} {path}")

                self._folder_cache[path] = folder_id

            # Recurse into children
            if isinstance(children, dict) and children:
                self.build_architecture(children, folder_id, path)

        return dict(self._folder_cache)

    @property
    def folder_map(self) -> Dict[str, str]:
        """Get the current folder path → ID mapping."""
        return dict(self._folder_cache)


# ---------------------------------------------------------------------------
# File Migrator
# ---------------------------------------------------------------------------
class FileMigrator:
    """
    Plans and executes file migrations.
    Supports dry-run mode, rollback tracking, and detailed reporting.
    """

    def __init__(
        self,
        ops: DriveOperations,
        config: Optional[DriveOrganizerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.ops = ops
        self.config = config or DriveOrganizerConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.categorizer = FileCategorizer(logger)
        self.music_organizer = MusicOrganizer(logger)
        self._actions: List[MigrationAction] = []
        self._completed: List[MigrationAction] = []
        self._errors: List[MigrationAction] = []

    def plan_migration(
        self,
        files: Dict[str, DriveFile],
        folder_map: Dict[str, str],
    ) -> List[MigrationAction]:
        """
        Create a migration plan for all files.
        Returns list of planned MigrationActions.
        """
        self._actions = []

        # Detect duplicates
        detector = DuplicateDetector(files, self.logger)
        duplicates = detector.detect()

        # Plan duplicate moves
        for dup_id, orig_id in duplicates:
            dup_file = files[dup_id]
            self._actions.append(MigrationAction(
                action_type="duplicate_flag",
                file_id=dup_id,
                file_name=dup_file.name,
                source_path=str(dup_file.parents),
                destination_path="11-DUPLICATES-DETECTED",
            ))

        # Categorize and plan moves
        for file_id, file in files.items():
            if file.is_duplicate:
                continue  # Already handled

            # Try music organizer first for music files
            dest = ""
            if file.extension in (".mp3", ".wav", ".flac", ".aac", ".ogg",
                                   ".m4a", ".wma", ".aiff", ".alac", ".opus"):
                dest = self.music_organizer.organize(file)

            # Fall back to general categorizer
            if not dest:
                dest = self.categorizer.categorize(file)

            if dest and dest in folder_map:
                self._actions.append(MigrationAction(
                    action_type="move",
                    file_id=file_id,
                    file_name=file.name,
                    source_path=str(file.parents),
                    destination_path=dest,
                ))

                # Plan rename if needed
                sanitized = sanitize_filename(file.name)
                if sanitized and sanitized != file.name and sanitized != file.name.lower():
                    self._actions.append(MigrationAction(
                        action_type="rename",
                        file_id=file_id,
                        file_name=file.name,
                        new_name=sanitized,
                    ))

        self.logger.info(f"Migration plan: {len(self._actions)} actions")
        return list(self._actions)

    def execute(
        self,
        folder_map: Dict[str, str],
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute the migration plan.
        Returns execution statistics.
        """
        stats = {
            "total_planned": len(self._actions),
            "executed": 0,
            "skipped": 0,
            "errors": 0,
            "dry_run": dry_run,
        }

        print(f"\n{C.BG_GREEN}{C.WHITE}{C.BOLD} EXECUTING MIGRATION {C.RESET}")
        if dry_run:
            print(f"  {C.YELLOW}{C.BOLD}DRY RUN — no changes will be made{C.RESET}")
        print(f"{C.CYAN}{'─' * 60}{C.RESET}")

        for i, action in enumerate(self._actions):
            if (i + 1) % 50 == 0 or i == 0:
                print(
                    f"  {C.MAGENTA}[{i + 1}/{len(self._actions)}]{C.RESET} "
                    f"Processing..."
                )

            try:
                if dry_run:
                    action.status = "dry_run"
                    stats["skipped"] += 1
                    continue

                if action.action_type == "move":
                    dest_id = folder_map.get(action.destination_path)
                    if dest_id:
                        old_parent = (
                            action.source_path.strip("[]'\"").split(",")[0].strip()
                            if action.source_path else None
                        )
                        self.ops.move_file(
                            action.file_id, dest_id, old_parent
                        )
                        action.status = "completed"
                        stats["executed"] += 1
                    else:
                        action.status = "skipped"
                        action.error = f"Destination not found: {action.destination_path}"
                        stats["skipped"] += 1

                elif action.action_type == "rename":
                    self.ops.rename_file(action.file_id, action.new_name)
                    action.status = "completed"
                    stats["executed"] += 1

                elif action.action_type == "duplicate_flag":
                    dest_id = folder_map.get("11-DUPLICATES-DETECTED")
                    if dest_id:
                        self.ops.move_file(action.file_id, dest_id)
                        action.status = "completed"
                        stats["executed"] += 1
                    else:
                        action.status = "skipped"
                        stats["skipped"] += 1

                self._completed.append(action)

            except Exception as e:
                action.status = "error"
                action.error = str(e)
                self._errors.append(action)
                stats["errors"] += 1
                self.logger.error(
                    f"Migration error for {action.file_name}: {e}"
                )

        return stats

    def save_plan(self, path: str = "migration_plan.json") -> None:
        """Save the migration plan to JSON."""
        data = [asdict(a) for a in self._actions]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.logger.info(f"Migration plan saved to {path}")

    @property
    def actions(self) -> List[MigrationAction]:
        """Get all planned actions."""
        return list(self._actions)

    @property
    def completed(self) -> List[MigrationAction]:
        """Get completed actions."""
        return list(self._completed)

    @property
    def errors(self) -> List[MigrationAction]:
        """Get failed actions."""
        return list(self._errors)
