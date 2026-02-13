"""
Configuration Management for Drive Organizer v2
=================================================
Externalized folder architecture, file type definitions, and all magic strings.
Uses JSON-loadable config with DriveOrganizerConfig dataclass.

Author : Angel Evans (Revvel / MIDNGHTSAPPHIRE)
License: MIT
Version: 2.0.0
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "2.0.0"
APP_NAME = "Drive Organizer"
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Google Drive MIME types
MIME_FOLDER = "application/vnd.google-apps.folder"
MIME_SHORTCUT = "application/vnd.google-apps.shortcut"
GOOGLE_EXPORT_MIMES = {
    "application/vnd.google-apps.document": "application/pdf",
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ),
    "application/vnd.google-apps.drawing": "image/png",
}

# ---------------------------------------------------------------------------
# Project sub-folder template — every project gets this structure
# ---------------------------------------------------------------------------
_PROJECT_SUBFOLDERS = {
    "Docs": {},
    "Code": {},
    "Assets": {},
    "Research": {},
    "Marketing": {},
    "Legal": {},
    "Notes": {},
}

# ---------------------------------------------------------------------------
# Industry-Standard Folder Architecture — NO ARCHIVING, ALL ACTIVE
# ---------------------------------------------------------------------------
FOLDER_ARCHITECTURE: Dict[str, Any] = {
    "01-BUSINESS": {
        "Ideas-Pipeline": {
            "Active": {},
            "Research": {},
            "Scorecards": {},
        },
        "Business-Plans": {},
        "Market-Research": {},
        "Financial-Models": {},
        "Branding-Identity": {},
        "Domains-SEO": {},
    },
    "02-PROJECTS": {
        "SSRN-Academic": {
            "Papers": {},
            "Research-Data": {},
            "Submissions": {},
            "eJournals": {},
        },
        "YumYumCode": dict(_PROJECT_SUBFOLDERS),
        "Universal-OZ": dict(_PROJECT_SUBFOLDERS),
        "MCT-InTheWild": dict(_PROJECT_SUBFOLDERS),
        "Meetaudreyevans": dict(_PROJECT_SUBFOLDERS),
        "Tiki-Washbot": dict(_PROJECT_SUBFOLDERS),
        "Neurooz": dict(_PROJECT_SUBFOLDERS),
        "Alt-Text-ADA": dict(_PROJECT_SUBFOLDERS),
        "Mechatronopolis": dict(_PROJECT_SUBFOLDERS),
        "Qahwa-Coffee": dict(_PROJECT_SUBFOLDERS),
        "Tiki-Wiki-Coffee": dict(_PROJECT_SUBFOLDERS),
        "Emergency-Response": dict(_PROJECT_SUBFOLDERS),
        "Pet-Insurance-App": dict(_PROJECT_SUBFOLDERS),
        "Gmail-Organizer": dict(_PROJECT_SUBFOLDERS),
        "Drive-Organizer": dict(_PROJECT_SUBFOLDERS),
    },
    "03-MUSIC": {
        "Catalog": {
            "Released": {},
            "Unreleased": {},
            "Work-In-Progress": {},
        },
        "By-Genre": {
            "Alt-Pop": {},
            "Alt-RnB": {},
            "Cinematic": {},
            "Indie-Folk-Rock": {},
            "KPop-Fusion": {},
        },
        "Lyrics": {},
        "Stems-Instrumentals": {},
        "Cover-Art": {},
        "Collaborations": {},
        "Distribution": {},
        "Copyright-Registrations": {},
        "Prompts-Templates": {},
    },
    "04-LEGAL": {
        "Court-Cases": {},
        "Trusts": {},
        "Contracts": {},
        "IP-Patents-Copyright": {},
        "Correspondence": {},
        "Timeline-Evidence": {},
    },
    "05-MEDICAL": {
        "Records": {},
        "Insurance": {},
        "Care-Plans": {},
        "Appointments": {},
        "Prescriptions": {},
    },
    "06-FINANCIAL": {
        "Tax-Returns": {},
        "Banking": {},
        "Investments": {},
        "Budgets": {},
        "Grants": {},
        "Receipts": {},
    },
    "07-CAREER": {
        "Resumes-CVs": {},
        "Cover-Letters": {},
        "Certifications": {},
        "Portfolio": {},
        "References": {},
        "Job-Applications": {},
    },
    "08-PERSONAL": {
        "Photos": {},
        "Videos": {},
        "K9-Grogu": {},
        "Church-One20": {},
        "Housing": {},
        "Contacts": {},
    },
    "09-DEVELOPMENT": {
        "Code-Snippets": {},
        "API-Keys-Credentials": {},
        "Architecture-Docs": {},
        "MCP-Servers": {},
        "DevOps": {},
        "GitHub-Repos": {},
    },
    "10-TEMPLATES": {
        "Documents": {},
        "Prompts": {},
        "Spreadsheets": {},
        "Presentations": {},
    },
    "11-DUPLICATES-DETECTED": {},
}

# ---------------------------------------------------------------------------
# File Extension Sets (case-insensitive matching enforced at use-site)
# ---------------------------------------------------------------------------
MUSIC_EXTENSIONS = frozenset({
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".aiff", ".alac",
    ".opus", ".mid", ".midi",
})
IMAGE_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg",
    ".heic", ".heif", ".raw", ".cr2", ".nef", ".psd", ".ai", ".eps",
})
VIDEO_EXTENSIONS = frozenset({
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v",
})
CODE_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
    ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php",
    ".swift", ".kt", ".r", ".sql", ".sh", ".bash", ".yml", ".yaml",
    ".json", ".xml", ".toml", ".ini", ".cfg", ".env", ".dockerfile",
})
DOCUMENT_EXTENSIONS = frozenset({
    ".doc", ".docx", ".pdf", ".txt", ".rtf", ".odt", ".pages",
})
SPREADSHEET_EXTENSIONS = frozenset({
    ".xls", ".xlsx", ".csv", ".ods", ".numbers",
})
PRESENTATION_EXTENSIONS = frozenset({
    ".ppt", ".pptx", ".key", ".odp",
})
STEM_EXTENSIONS = frozenset({
    ".stem.mp4", ".als", ".flp", ".logic", ".ptx", ".rpp",
})

# ---------------------------------------------------------------------------
# Keyword → Destination Rules
# ---------------------------------------------------------------------------
KEYWORD_RULES: List[tuple] = [
    # Music-related
    (["song", "track", "beat", "instrumental", "remix", "master", "mix"],
     "03-MUSIC/Catalog/Work-In-Progress"),
    (["lyric", "lyrics", "songwriting"], "03-MUSIC/Lyrics"),
    (["stem", "instrumental", "acapella", "a cappella"],
     "03-MUSIC/Stems-Instrumentals"),
    (["cover art", "album art", "artwork", "single art"], "03-MUSIC/Cover-Art"),
    (["collab", "collaboration", "feat", "featuring"],
     "03-MUSIC/Collaborations"),
    (["distrokid", "tunecore", "cdbaby", "distribution"],
     "03-MUSIC/Distribution"),
    (["copyright", "registration", "ascap", "bmi", "sesac"],
     "03-MUSIC/Copyright-Registrations"),
    (["prompt", "template", "ai prompt", "suno", "udio"],
     "03-MUSIC/Prompts-Templates"),
    # Business
    (["business plan", "pitch deck", "executive summary"],
     "01-BUSINESS/Business-Plans"),
    (["market research", "competitor analysis", "market analysis"],
     "01-BUSINESS/Market-Research"),
    (["financial model", "pro forma", "projection", "forecast"],
     "01-BUSINESS/Financial-Models"),
    (["brand", "logo", "identity", "style guide", "brand kit"],
     "01-BUSINESS/Branding-Identity"),
    (["domain", "seo", "keyword", "sitemap"], "01-BUSINESS/Domains-SEO"),
    (["idea", "concept", "brainstorm", "pipeline"],
     "01-BUSINESS/Ideas-Pipeline/Active"),
    (["scorecard", "evaluation", "scoring"],
     "01-BUSINESS/Ideas-Pipeline/Scorecards"),
    # Project-specific
    (["ssrn", "academic", "paper", "journal", "research paper"],
     "02-PROJECTS/SSRN-Academic/Papers"),
    (["yumyum", "yum yum", "yumyumcode"], "02-PROJECTS/YumYumCode/Docs"),
    (["universal oz", "universaloz"], "02-PROJECTS/Universal-OZ/Docs"),
    (["mct", "inthewild", "in the wild"], "02-PROJECTS/MCT-InTheWild/Docs"),
    (["audrey", "meetaudrey", "meetaudreyevans"],
     "02-PROJECTS/Meetaudreyevans/Docs"),
    (["tiki", "washbot", "tiki wash"], "02-PROJECTS/Tiki-Washbot/Docs"),
    (["neurooz", "neuro oz"], "02-PROJECTS/Neurooz/Docs"),
    (["alt text", "alt-text", "ada compliance", "accessibility"],
     "02-PROJECTS/Alt-Text-ADA/Docs"),
    (["mechatronopolis", "mechatron"], "02-PROJECTS/Mechatronopolis/Docs"),
    (["qahwa", "quhwa"], "02-PROJECTS/Qahwa-Coffee/Docs"),
    (["tiki wiki coffee", "tiki coffee"], "02-PROJECTS/Tiki-Wiki-Coffee/Docs"),
    (["emergency response", "gunshot detection"],
     "02-PROJECTS/Emergency-Response/Docs"),
    (["pet insurance"], "02-PROJECTS/Pet-Insurance-App/Docs"),
    # Legal
    (["court", "case", "lawsuit", "litigation", "filing"],
     "04-LEGAL/Court-Cases"),
    (["trust", "estate plan", "will", "beneficiary"], "04-LEGAL/Trusts"),
    (["contract", "agreement", "nda", "terms of service", "tos"],
     "04-LEGAL/Contracts"),
    (["patent", "trademark", "intellectual property", "ip"],
     "04-LEGAL/IP-Patents-Copyright"),
    (["legal letter", "attorney", "lawyer", "legal correspondence"],
     "04-LEGAL/Correspondence"),
    (["evidence", "timeline", "exhibit"], "04-LEGAL/Timeline-Evidence"),
    # Medical
    (["medical", "health", "diagnosis", "lab result", "prescription"],
     "05-MEDICAL/Records"),
    (["insurance", "health insurance", "coverage", "claim"],
     "05-MEDICAL/Insurance"),
    (["care plan", "treatment", "therapy", "medication"],
     "05-MEDICAL/Care-Plans"),
    (["appointment", "doctor visit", "checkup"], "05-MEDICAL/Appointments"),
    # Financial
    (["tax", "tax return", "w2", "w-2", "1099", "irs"],
     "06-FINANCIAL/Tax-Returns"),
    (["bank", "banking", "statement", "checking", "savings"],
     "06-FINANCIAL/Banking"),
    (["invest", "stock", "portfolio", "401k", "ira", "crypto"],
     "06-FINANCIAL/Investments"),
    (["budget", "expense", "spending"], "06-FINANCIAL/Budgets"),
    (["grant", "funding", "scholarship", "award"], "06-FINANCIAL/Grants"),
    (["receipt", "invoice", "purchase order"], "06-FINANCIAL/Receipts"),
    # Career
    (["resume", "cv", "curriculum vitae"], "07-CAREER/Resumes-CVs"),
    (["cover letter", "application letter"], "07-CAREER/Cover-Letters"),
    (["certificate", "certification", "credential", "license"],
     "07-CAREER/Certifications"),
    (["portfolio", "work sample"], "07-CAREER/Portfolio"),
    (["reference", "recommendation", "referral"], "07-CAREER/References"),
    # Personal
    (["photo", "selfie", "picture", "image", "screenshot"],
     "08-PERSONAL/Photos"),
    (["grogu", "dog", "puppy", "k9", "pet", "vet"], "08-PERSONAL/K9-Grogu"),
    (["church", "one20", "faith", "ministry", "sermon"],
     "08-PERSONAL/Church-One20"),
    (["housing", "apartment", "lease", "rent", "mortgage", "house"],
     "08-PERSONAL/Housing"),
    (["contact", "address book", "phone number"], "08-PERSONAL/Contacts"),
    # Development
    (["code", "script", "snippet", "function", "module"],
     "09-DEVELOPMENT/Code-Snippets"),
    (["api key", "credential", "secret", "token", "password"],
     "09-DEVELOPMENT/API-Keys-Credentials"),
    (["architecture", "system design", "diagram"],
     "09-DEVELOPMENT/Architecture-Docs"),
    (["mcp", "model context", "server config"], "09-DEVELOPMENT/MCP-Servers"),
    (["devops", "docker", "kubernetes", "ci/cd", "pipeline"],
     "09-DEVELOPMENT/DevOps"),
    (["github", "repo", "repository", "git"], "09-DEVELOPMENT/GitHub-Repos"),
    # Templates
    (["template doc", "boilerplate", "form template"],
     "10-TEMPLATES/Documents"),
    (["prompt template", "ai template"], "10-TEMPLATES/Prompts"),
]

# ---------------------------------------------------------------------------
# Genre & Release Status Patterns (compiled regex, case-insensitive)
# ---------------------------------------------------------------------------
GENRE_PATTERNS: Dict[str, List[str]] = {
    "Alt-Pop": [
        "alt pop", "alt-pop", "alternative pop", "indie pop", "synth pop",
        "electropop", "dream pop",
    ],
    "Alt-RnB": [
        "alt rnb", "alt-rnb", "alt r&b", "alternative rnb", "neo soul",
        "alternative r&b",
    ],
    "Cinematic": [
        "cinematic", "film score", "soundtrack", "orchestral", "epic",
        "trailer music", "ambient score",
    ],
    "Indie-Folk-Rock": [
        "indie folk", "indie rock", "folk rock", "indie-folk", "folk-rock",
        "acoustic rock", "americana",
    ],
    "KPop-Fusion": [
        "kpop", "k-pop", "kpop fusion", "k-pop fusion", "korean pop",
        "j-pop", "jpop",
    ],
}

RELEASE_STATUS_PATTERNS: Dict[str, List[str]] = {
    "Released": [
        "released", "final", "master", "mastered", "official",
        "distributed", "live on", "out now",
    ],
    "Work-In-Progress": [
        "wip", "work in progress", "draft", "demo", "rough",
        "sketch", "unfinished", "incomplete",
    ],
    "Unreleased": [
        "unreleased", "vault", "shelved", "unreleased", "not released",
    ],
}


# ---------------------------------------------------------------------------
# DriveOrganizerConfig dataclass
# ---------------------------------------------------------------------------
@dataclass
class DriveOrganizerConfig:
    """Central configuration for the Drive Organizer."""

    api_calls_per_second: int = 8
    batch_size: int = 100
    max_retries: int = 7
    base_delay: float = 1.0
    folder_architecture: Dict[str, Any] = field(
        default_factory=lambda: dict(FOLDER_ARCHITECTURE)
    )
    credentials_file: str = "credentials.json"
    token_file: str = "token.json"
    output_dir: str = "."
    dry_run: bool = True
    verbose: bool = False
    music_only: bool = False
    scan_only: bool = False

    @classmethod
    def from_json(cls, path: str) -> "DriveOrganizerConfig":
        """Load configuration from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self, path: str) -> None:
        """Save configuration to a JSON file."""
        from dataclasses import asdict
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)


def save_default_config(path: str = "drive_organizer_config.json") -> None:
    """Write the default configuration to a JSON file."""
    cfg = DriveOrganizerConfig()
    cfg.to_json(path)
