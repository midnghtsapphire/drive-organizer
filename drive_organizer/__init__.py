"""
Drive Organizer v2
===================
Google Drive Analysis, Reorganization & Migration Tool.

Modular package structure implementing all Venice AI code review recommendations:
- Encrypted credential storage
- Token bucket rate limiting
- Compiled regex patterns with case-insensitive matching
- Comprehensive error handling with exponential backoff
- No archiving — all projects active with detailed subfolders
"""

from .config import (
    VERSION,
    APP_NAME,
    SCOPES,
    FOLDER_ARCHITECTURE,
    MUSIC_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    CODE_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    KEYWORD_RULES,
    GENRE_PATTERNS,
    MIME_FOLDER,
    DriveOrganizerConfig,
)
from .utils import (
    sanitize_filename,
    compute_md5_from_bytes,
    format_size,
    setup_logging,
    C,
)
from .auth import DriveAuthenticator
from .categorizer import (
    DriveFile,
    DriveFolder,
    MigrationAction,
    ScanReport,
    FileCategorizer,
    DuplicateDetector,
)
from .music_organizer import MusicOrganizer
from .operations import (
    TokenBucketRateLimiter,
    DriveOperations,
    api_call_with_backoff,
)
from .migrator import FolderArchitect, FileMigrator
from .reporter import ReportGenerator

__version__ = VERSION
__all__ = [
    # Config
    "VERSION",
    "APP_NAME",
    "SCOPES",
    "FOLDER_ARCHITECTURE",
    "MUSIC_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "VIDEO_EXTENSIONS",
    "CODE_EXTENSIONS",
    "DOCUMENT_EXTENSIONS",
    "KEYWORD_RULES",
    "GENRE_PATTERNS",
    "MIME_FOLDER",
    "DriveOrganizerConfig",
    # Utils
    "sanitize_filename",
    "compute_md5_from_bytes",
    "format_size",
    "setup_logging",
    "C",
    # Auth
    "DriveAuthenticator",
    # Categorizer
    "DriveFile",
    "DriveFolder",
    "MigrationAction",
    "ScanReport",
    "FileCategorizer",
    "DuplicateDetector",
    # Music
    "MusicOrganizer",
    # Operations
    "TokenBucketRateLimiter",
    "DriveOperations",
    "api_call_with_backoff",
    # Migrator
    "FolderArchitect",
    "FileMigrator",
    # Reporter
    "ReportGenerator",
]
