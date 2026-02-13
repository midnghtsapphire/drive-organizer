"""
Utility Functions for Drive Organizer v2
=========================================
Compiled regex patterns, filename sanitization, size formatting,
MD5 computation, and color output helpers.
"""

from __future__ import annotations

import hashlib
import logging
import re
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# Compiled Regex Patterns (case-insensitive)
# ---------------------------------------------------------------------------
RE_DATE_YYYYMMDD = re.compile(r"^(\d{4})(\d{2})(\d{2})[_\-]?", re.IGNORECASE)
RE_DATE_YYYY_MM_DD = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[_\-]?", re.IGNORECASE)
RE_SPECIAL_CHARS = re.compile(r"[^\w\s\-.]", re.UNICODE)
RE_MULTI_HYPHENS = re.compile(r"-{2,}")
RE_MULTI_SPACES = re.compile(r"\s+")
RE_PARENS = re.compile(r"\([^)]*\)")
RE_BRACKETS = re.compile(r"\[[^\]]*\]")


# ---------------------------------------------------------------------------
# ANSI Color Codes
# ---------------------------------------------------------------------------
class C:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_MAGENTA = "\033[45m"
    BG_RED = "\033[41m"


# ---------------------------------------------------------------------------
# Color Formatter for Logging
# ---------------------------------------------------------------------------
class ColorFormatter(logging.Formatter):
    """Colored log formatter for terminal output."""
    LEVEL_COLORS = {
        logging.DEBUG:    C.GRAY,
        logging.INFO:     C.CYAN,
        logging.WARNING:  C.YELLOW,
        logging.ERROR:    C.RED,
        logging.CRITICAL: C.RED + C.BOLD,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, C.RESET)
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        return (
            f"{C.GRAY}{ts}{C.RESET} "
            f"{color}{record.levelname:<8}{C.RESET} "
            f"{record.getMessage()}"
        )


def setup_logging(
    name: str = "drive_organizer",
    log_file: str = "drive_organizer.log",
) -> logging.Logger:
    """Configure dual logging: file + colored console."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger

    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(ColorFormatter())
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# Filename Sanitization
# ---------------------------------------------------------------------------
def sanitize_filename(name: str) -> str:
    """
    Sanitize a filename to kebab-case with optional date prefix.

    - Extracts date prefix if present (YYYYMMDD or YYYY-MM-DD)
    - Removes parentheses/brackets content
    - Strips special characters
    - Converts to lowercase kebab-case
    - Preserves file extension
    """
    if not name:
        return ""

    # Split extension
    dot_idx = name.rfind(".")
    if dot_idx > 0:
        base = name[:dot_idx]
        ext = name[dot_idx:].lower()
    else:
        base = name
        ext = ""

    # Extract date prefix
    date_prefix = ""
    m = RE_DATE_YYYY_MM_DD.match(base)
    if m:
        date_prefix = f"{m.group(1)}-{m.group(2)}-{m.group(3)}_"
        base = base[m.end():]
    else:
        m = RE_DATE_YYYYMMDD.match(base)
        if m:
            date_prefix = f"{m.group(1)}-{m.group(2)}-{m.group(3)}_"
            base = base[m.end():]

    # Remove parentheses and brackets content
    base = RE_PARENS.sub("", base)
    base = RE_BRACKETS.sub("", base)

    # Remove special characters
    base = RE_SPECIAL_CHARS.sub(" ", base)

    # Collapse whitespace, convert to kebab-case
    base = RE_MULTI_SPACES.sub(" ", base).strip()
    base = base.replace("_", " ").replace(" ", "-").lower()

    # Collapse multiple hyphens
    base = RE_MULTI_HYPHENS.sub("-", base).strip("-")

    if not base:
        return ext.lstrip(".") if ext else ""

    return f"{date_prefix}{base}{ext}"


# ---------------------------------------------------------------------------
# MD5 Computation
# ---------------------------------------------------------------------------
def compute_md5_from_bytes(data: bytes) -> str:
    """Compute MD5 hex digest from bytes."""
    return hashlib.md5(data).hexdigest()


# ---------------------------------------------------------------------------
# Size Formatting
# ---------------------------------------------------------------------------
def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable string."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
def print_banner(version: str) -> None:
    """Print the application banner."""
    banner = f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ██████╗ ██╗██╗   ██╗███████╗                      ║
║   ██╔══██╗██╔══██╗██║██║   ██║██╔════╝                      ║
║   ██║  ██║██████╔╝██║██║   ██║█████╗                        ║
║   ██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝                        ║
║   ██████╔╝██║  ██║██║ ╚████╔╝ ███████╗                      ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝                      ║
║                                                              ║
║   {C.WHITE}O R G A N I Z E R{C.CYAN}   v{version}                             ║
║   {C.GRAY}Google Drive Analysis, Reorganization & Migration{C.CYAN}          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{C.RESET}
"""
    print(banner)
