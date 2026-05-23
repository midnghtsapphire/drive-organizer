# Drive Organizer v2.0.0

**Google Drive Analysis, Reorganization & Migration Tool**

A modular Python application that scans, analyzes, categorizes, and reorganizes your entire Google Drive into a clean, industry-standard folder hierarchy. Built with security, performance, and extensibility in mind.

## Revvel Standards (S2M)

This repository has been run through the revvel-standards baseline documentation set:

- [CHANGELOG.md](CHANGELOG.md)
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [GO_TO_MARKET.md](GO_TO_MARKET.md)
- [BRAND_GUIDELINES.md](BRAND_GUIDELINES.md)
- [SECURITY.md](SECURITY.md)

**Website in Test (Vercel):** Not yet deployed (current product surface is CLI-first).

## Features

- **Modular Architecture** — Clean package structure with separated concerns (auth, categorizer, operations, music, migrator, reporter)
- **Encrypted Credential Storage** — Fernet symmetric encryption for OAuth tokens
- **Token Bucket Rate Limiter** — Proactive API rate limiting with burst support
- **Deep Music Organization** — Genre detection, release status, stem/instrumental separation
- **Compiled Regex Patterns** — Case-insensitive matching with pre-compiled patterns for performance
- **Exponential Backoff** — Automatic retry with backoff on API rate limits (429, 500, 503)
- **Duplicate Detection** — MD5 checksum and name+size matching
- **Dry Run Mode** — Preview all changes before executing (default)
- **Comprehensive Reporting** — JSON and Markdown export

## Folder Architecture

All projects are **active** — no archiving, no catch-all buckets. Every file has a precise home.

```
01-BUSINESS/
├── Ideas-Pipeline/Active/
├── Business-Plans/
├── Market-Research/
├── Financial-Models/
├── Branding-Identity/
└── Domains-SEO/

02-PROJECTS/
├── SSRN-Academic/{Papers,Research-Data,Submissions,eJournals}/
├── YumYumCode/{Docs,Code,Assets,Research,Marketing,Legal,Notes}/
├── Universal-OZ/{...}/
├── MCT-InTheWild/{...}/
├── Meetaudreyevans/{...}/
├── Tiki-Washbot/{...}/
├── Neurooz/{...}/
├── Alt-Text-ADA/{...}/
├── Mechatronopolis/{...}/
├── Qahwa-Coffee/{...}/
├── Tiki-Wiki-Coffee/{...}/
├── Emergency-Response/{...}/
├── Pet-Insurance-App/{...}/
├── Gmail-Organizer/{...}/
└── Drive-Organizer/{...}/

03-MUSIC/
├── Catalog/{Released,Unreleased,Work-In-Progress}/
├── By-Genre/{Alt-Pop,Alt-RnB,Cinematic,Indie-Folk-Rock,KPop-Fusion}/
├── Lyrics/
├── Stems-Instrumentals/
├── Cover-Art/
├── Collaborations/
├── Distribution/
├── Copyright-Registrations/
└── Prompts-Templates/

04-LEGAL/{Court-Cases,Trusts,Contracts,IP-Patents-Copyright,...}/
05-MEDICAL/{Records,Insurance,Care-Plans,Appointments,Prescriptions}/
06-FINANCIAL/{Tax-Returns,Banking,Investments,Budgets,Grants,Receipts}/
07-CAREER/{Resumes-CVs,Cover-Letters,Certifications,Portfolio,...}/
08-PERSONAL/{Photos,Videos,K9-Grogu,Church-One20,Housing,Contacts}/
09-DEVELOPMENT/{Code-Snippets,API-Keys-Credentials,Architecture-Docs,...}/
10-TEMPLATES/{Documents,Prompts,Spreadsheets,Presentations}/
11-DUPLICATES-DETECTED/
```

## Installation

```bash
pip install -e .
```

### Prerequisites

1. Python 3.9+
2. Google Cloud project with Drive API enabled
3. OAuth 2.0 credentials (`credentials.json`)

### Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable Google Drive API
3. Create OAuth 2.0 credentials (Desktop application)
4. Download `credentials.json` to the project directory

## Usage

### Scan Only (no changes)
```bash
python -m drive_organizer --scan-only
```

### Dry Run (preview changes)
```bash
python -m drive_organizer --dry-run
```

### Execute Migration
```bash
python -m drive_organizer --execute
```

### Build Folder Architecture Only
```bash
python -m drive_organizer --build-folders
```

### Music-Only Mode
```bash
python -m drive_organizer --music-only --execute
```

### Custom Config
```bash
python -m drive_organizer --config my_config.json --execute
```

## Before/After Example

**Before:**
```
My Drive/
├── song final mix (2).mp3
├── Resume_2024_FINAL_v3.docx
├── random_screenshot.png
├── api_key_backup.txt
├── Court Filing Jan 2024.pdf
└── Untitled document
```

**After:**
```
My Drive/
├── 03-MUSIC/Catalog/Work-In-Progress/song-final-mix.mp3
├── 07-CAREER/Resumes-CVs/2024_resume-final-v3.docx
├── 08-PERSONAL/Photos/random-screenshot.png
├── 09-DEVELOPMENT/API-Keys-Credentials/api-key-backup.txt
├── 04-LEGAL/Court-Cases/2024-01_court-filing-jan-2024.pdf
├── 10-TEMPLATES/Documents/untitled-document
└── 11-DUPLICATES-DETECTED/song-final-mix-2.mp3
```

## Configuration

Edit `drive_organizer_config.json`:

```json
{
  "api_calls_per_second": 8,
  "batch_size": 100,
  "max_retries": 7,
  "base_delay": 1.0,
  "credentials_file": "credentials.json",
  "token_file": "token.json",
  "dry_run": true
}
```

## Security Considerations

- **Encrypted Tokens** — OAuth tokens are encrypted at rest using Fernet (AES-128-CBC)
- **File Permissions** — Token and key files are set to `0600` (owner-only read/write)
- **No Hardcoded Secrets** — All credentials are externalized
- **Secure Refresh** — Automatic token refresh with encrypted re-storage

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v --cov=drive_organizer --cov-report=term-missing

# Run with hypothesis property-based tests
python -m pytest tests/ -v --hypothesis-show-statistics
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass with 90%+ coverage
5. Submit a pull request

## Roadmap

- [ ] Web UI dashboard for migration preview
- [ ] Scheduled automatic organization via cron
- [ ] Google Workspace admin support (multi-user)
- [ ] AI-powered file categorization using LLM
- [ ] Integration with Gmail Organizer for unified management

## Troubleshooting

| Error Code | Description | Solution |
|-----------|-------------|----------|
| `403` | Insufficient permissions | Re-run OAuth flow, ensure Drive API scope is granted |
| `404` | File/folder not found | File may have been deleted or moved; re-scan |
| `429` | Rate limit exceeded | Reduce `api_calls_per_second` in config |
| `500` | Server error | Automatic retry with backoff; check Google status |
| `FATAL: credentials.json not found` | Missing OAuth credentials | Download from Google Cloud Console |

## License

MIT License

Copyright (c) 2025-2026 Angel Evans

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Test

| Feature | Status |
|---------|--------|
| Feature | ✅ Ready |
