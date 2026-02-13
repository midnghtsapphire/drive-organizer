"""
File Categorizer Module for Drive Organizer v2
================================================
File classification using compiled regex patterns with case-insensitive matching.
Supports MIME-type, extension, and keyword-based categorization.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .config import (
    CODE_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    IMAGE_EXTENSIONS,
    KEYWORD_RULES,
    MUSIC_EXTENSIONS,
    PRESENTATION_EXTENSIONS,
    SPREADSHEET_EXTENSIONS,
    STEM_EXTENSIONS,
    VIDEO_EXTENSIONS,
)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------
@dataclass
class DriveFile:
    """Represents a file in Google Drive."""
    id: str
    name: str
    mime_type: str
    size: int = 0
    md5_checksum: str = ""
    parents: List[str] = field(default_factory=list)
    created_time: str = ""
    modified_time: str = ""
    is_duplicate: bool = False
    duplicate_of: str = ""
    suggested_destination: str = ""

    @property
    def extension(self) -> str:
        """Extract lowercase file extension."""
        dot_idx = self.name.rfind(".")
        if dot_idx > 0:
            return self.name[dot_idx:].lower()
        return ""

    @property
    def is_google_doc(self) -> bool:
        """Check if this is a Google Workspace document."""
        return self.mime_type.startswith("application/vnd.google-apps.")


@dataclass
class DriveFolder:
    """Represents a folder in Google Drive."""
    id: str
    name: str
    parents: List[str] = field(default_factory=list)
    children_folders: List[str] = field(default_factory=list)
    children_files: List[str] = field(default_factory=list)


@dataclass
class MigrationAction:
    """Represents a planned migration action."""
    action_type: str  # move, rename, duplicate_flag
    file_id: str = ""
    file_name: str = ""
    source_path: str = ""
    destination_path: str = ""
    new_name: str = ""
    status: str = "pending"
    error: str = ""


@dataclass
class ScanReport:
    """Aggregated scan results."""
    total_files: int = 0
    total_folders: int = 0
    total_size_bytes: int = 0
    file_type_counts: Dict[str, int] = field(default_factory=dict)
    duplicate_count: int = 0
    uncategorized_count: int = 0
    music_files: int = 0
    document_files: int = 0
    image_files: int = 0
    code_files: int = 0


# ---------------------------------------------------------------------------
# Compiled Keyword Rules
# ---------------------------------------------------------------------------
_COMPILED_KEYWORD_RULES: List[Tuple[List[re.Pattern], str]] = []


def _compile_keyword_rules() -> List[Tuple[List[re.Pattern], str]]:
    """Compile keyword rules into regex patterns (once)."""
    global _COMPILED_KEYWORD_RULES
    if _COMPILED_KEYWORD_RULES:
        return _COMPILED_KEYWORD_RULES

    for keywords, destination in KEYWORD_RULES:
        patterns = [
            re.compile(re.escape(kw), re.IGNORECASE)
            for kw in keywords
        ]
        _COMPILED_KEYWORD_RULES.append((patterns, destination))

    return _COMPILED_KEYWORD_RULES


# ---------------------------------------------------------------------------
# File Categorizer
# ---------------------------------------------------------------------------
class FileCategorizer:
    """
    Categorizes files into the folder architecture based on:
    1. MIME type
    2. File extension (case-insensitive)
    3. Filename keyword matching (compiled regex, case-insensitive)
    """

    # MIME type → destination mapping
    MIME_DESTINATIONS: Dict[str, str] = {
        "application/vnd.google-apps.document": "10-TEMPLATES/Documents",
        "application/vnd.google-apps.spreadsheet": "10-TEMPLATES/Spreadsheets",
        "application/vnd.google-apps.presentation": "10-TEMPLATES/Presentations",
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._keyword_rules = _compile_keyword_rules()

    def categorize(self, file: DriveFile) -> str:
        """
        Determine the destination folder for a file.

        Priority:
        1. Keyword match in filename (most specific)
        2. Extension-based categorization
        3. MIME-type fallback
        4. Empty string if uncategorizable
        """
        # 1. Try keyword matching first (most specific)
        dest = self._match_keywords(file.name)
        if dest:
            return dest

        # 2. Extension-based
        ext = file.extension
        if ext:
            dest = self._categorize_by_extension(ext)
            if dest:
                return dest

        # 3. MIME-type fallback
        dest = self.MIME_DESTINATIONS.get(file.mime_type, "")
        if dest:
            return dest

        return ""

    def _match_keywords(self, filename: str) -> str:
        """Match filename against compiled keyword rules."""
        for patterns, destination in self._keyword_rules:
            for pattern in patterns:
                if pattern.search(filename):
                    return destination
        return ""

    def _categorize_by_extension(self, ext: str) -> str:
        """Categorize by file extension (case-insensitive)."""
        ext_lower = ext.lower()

        if ext_lower in MUSIC_EXTENSIONS:
            return "03-MUSIC/Catalog/Work-In-Progress"
        if ext_lower in STEM_EXTENSIONS:
            return "03-MUSIC/Stems-Instrumentals"
        if ext_lower in IMAGE_EXTENSIONS:
            return "08-PERSONAL/Photos"
        if ext_lower in VIDEO_EXTENSIONS:
            return "08-PERSONAL/Videos"
        if ext_lower in CODE_EXTENSIONS:
            return "09-DEVELOPMENT/Code-Snippets"
        if ext_lower in DOCUMENT_EXTENSIONS:
            return "10-TEMPLATES/Documents"
        if ext_lower in SPREADSHEET_EXTENSIONS:
            return "10-TEMPLATES/Spreadsheets"
        if ext_lower in PRESENTATION_EXTENSIONS:
            return "10-TEMPLATES/Presentations"

        return ""

    def categorize_batch(
        self, files: Dict[str, DriveFile]
    ) -> Dict[str, str]:
        """Categorize a batch of files. Returns file_id → destination mapping."""
        results: Dict[str, str] = {}
        for file_id, file in files.items():
            dest = self.categorize(file)
            if dest:
                file.suggested_destination = dest
            results[file_id] = dest
        return results


# ---------------------------------------------------------------------------
# Duplicate Detector
# ---------------------------------------------------------------------------
class DuplicateDetector:
    """
    Detects duplicate files using:
    1. MD5 checksum matching
    2. Name + size matching (for Google Docs without checksums)
    """

    def __init__(
        self,
        files: Dict[str, DriveFile],
        logger: Optional[logging.Logger] = None,
    ):
        self.files = files
        self.logger = logger or logging.getLogger(__name__)

    def detect(self) -> List[Tuple[str, str]]:
        """
        Detect duplicates. Returns list of (duplicate_id, original_id) tuples.
        The file with the older modified_time is considered the duplicate.
        """
        duplicates: List[Tuple[str, str]] = []

        # Group by MD5
        md5_groups: Dict[str, List[str]] = {}
        no_md5: List[str] = []

        for fid, f in self.files.items():
            if f.md5_checksum:
                md5_groups.setdefault(f.md5_checksum, []).append(fid)
            else:
                no_md5.append(fid)

        # MD5-based duplicates
        for md5, file_ids in md5_groups.items():
            if len(file_ids) > 1:
                # Sort by modified_time descending — newest is the "original"
                sorted_ids = sorted(
                    file_ids,
                    key=lambda fid: self.files[fid].modified_time or "",
                    reverse=True,
                )
                original = sorted_ids[0]
                for dup_id in sorted_ids[1:]:
                    duplicates.append((dup_id, original))
                    self.files[dup_id].is_duplicate = True
                    self.files[dup_id].duplicate_of = original

        # Name + size matching for files without MD5
        name_size_groups: Dict[str, List[str]] = {}
        for fid in no_md5:
            f = self.files[fid]
            key = f"{f.name.lower()}|{f.size}"
            name_size_groups.setdefault(key, []).append(fid)

        for key, file_ids in name_size_groups.items():
            if len(file_ids) > 1:
                sorted_ids = sorted(
                    file_ids,
                    key=lambda fid: self.files[fid].modified_time or "",
                    reverse=True,
                )
                original = sorted_ids[0]
                for dup_id in sorted_ids[1:]:
                    duplicates.append((dup_id, original))
                    self.files[dup_id].is_duplicate = True
                    self.files[dup_id].duplicate_of = original

        self.logger.info(f"Found {len(duplicates)} duplicate files")
        return duplicates
