"""
Music Organizer Module for Drive Organizer v2
===============================================
Deep music organization: genre detection, release status,
stem/instrumental separation, cover art handling.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

from .categorizer import DriveFile
from .config import (
    GENRE_PATTERNS,
    MUSIC_EXTENSIONS,
    RELEASE_STATUS_PATTERNS,
    STEM_EXTENSIONS,
)


# ---------------------------------------------------------------------------
# Compiled Genre & Status Patterns
# ---------------------------------------------------------------------------
_COMPILED_GENRE: Dict[str, List[re.Pattern]] = {}
_COMPILED_STATUS: Dict[str, List[re.Pattern]] = {}


def _compile_music_patterns() -> None:
    """Compile genre and release status patterns once."""
    global _COMPILED_GENRE, _COMPILED_STATUS

    if not _COMPILED_GENRE:
        for genre, keywords in GENRE_PATTERNS.items():
            _COMPILED_GENRE[genre] = [
                re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords
            ]

    if not _COMPILED_STATUS:
        for status, keywords in RELEASE_STATUS_PATTERNS.items():
            _COMPILED_STATUS[status] = [
                re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords
            ]


# ---------------------------------------------------------------------------
# Music Organizer
# ---------------------------------------------------------------------------
class MusicOrganizer:
    """
    Deep music file organization.

    Organizes music files into:
    - 03-MUSIC/By-Genre/{genre}/
    - 03-MUSIC/Catalog/{status}/
    - 03-MUSIC/Stems-Instrumentals/
    - 03-MUSIC/Cover-Art/
    - 03-MUSIC/Lyrics/
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        _compile_music_patterns()

    def organize(self, file: DriveFile) -> str:
        """
        Determine the optimal music folder for a file.
        Returns the destination path within the architecture.
        """
        ext = file.extension
        name_lower = file.name.lower()

        # Check if it's a stem/instrumental file
        if self._is_stem(file):
            return "03-MUSIC/Stems-Instrumentals"

        # Check if it's cover art
        if self._is_cover_art(file):
            return "03-MUSIC/Cover-Art"

        # Check if it's lyrics
        if self._is_lyrics(file):
            return "03-MUSIC/Lyrics"

        # Check if it's a music file
        if ext not in MUSIC_EXTENSIONS:
            return ""

        # Try genre detection
        genre = self.detect_genre(file.name)
        if genre:
            return f"03-MUSIC/By-Genre/{genre}"

        # Try release status detection
        status = self.detect_release_status(file.name)
        if status:
            return f"03-MUSIC/Catalog/{status}"

        # Default for music files
        return "03-MUSIC/Catalog/Work-In-Progress"

    def detect_genre(self, filename: str) -> str:
        """Detect genre from filename using compiled patterns."""
        for genre, patterns in _COMPILED_GENRE.items():
            for pattern in patterns:
                if pattern.search(filename):
                    return genre
        return ""

    def detect_release_status(self, filename: str) -> str:
        """Detect release status from filename using compiled patterns."""
        for status, patterns in _COMPILED_STATUS.items():
            for pattern in patterns:
                if pattern.search(filename):
                    return status
        return ""

    def _is_stem(self, file: DriveFile) -> bool:
        """Check if file is a stem/instrumental."""
        ext = file.extension
        name_lower = file.name.lower()

        if ext in STEM_EXTENSIONS:
            return True

        stem_keywords = [
            "stem", "instrumental", "acapella", "a cappella",
            "backing track", "karaoke",
        ]
        return any(kw in name_lower for kw in stem_keywords)

    def _is_cover_art(self, file: DriveFile) -> bool:
        """Check if file is cover art."""
        from .config import IMAGE_EXTENSIONS
        if file.extension not in IMAGE_EXTENSIONS:
            return False

        art_keywords = [
            "cover", "album art", "artwork", "single art",
            "cover art", "thumbnail",
        ]
        name_lower = file.name.lower()
        return any(kw in name_lower for kw in art_keywords)

    def _is_lyrics(self, file: DriveFile) -> bool:
        """Check if file is a lyrics document."""
        name_lower = file.name.lower()
        ext = file.extension

        if ext in (".txt", ".doc", ".docx", ".pdf"):
            return any(kw in name_lower for kw in ["lyric", "lyrics", "songwriting"])

        return False

    def organize_batch(
        self, files: Dict[str, DriveFile]
    ) -> Dict[str, str]:
        """Organize a batch of music-related files."""
        results: Dict[str, str] = {}
        for file_id, file in files.items():
            dest = self.organize(file)
            if dest:
                file.suggested_destination = dest
                results[file_id] = dest
        return results
