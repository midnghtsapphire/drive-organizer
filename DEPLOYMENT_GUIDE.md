# Deployment Guide

This project is a Python CLI package (`drive-organizer`) designed for local or CI execution.

## 1) Prerequisites

- Python 3.9+
- `credentials.json` from Google Cloud OAuth desktop app setup
- Access to Google Drive API for the target account

## 2) Install

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## 3) Environment and Secrets

- Do **not** commit `credentials.json`, token files, or encryption keys.
- Keep secrets in environment variables or local secure files only.
- Ensure file permissions for local key/token artifacts are owner-only.

## 4) Validate

```bash
python -m pytest
python -m build
```

## 5) Run

```bash
python -m drive_organizer --dry-run
python -m drive_organizer --execute
```

## 6) Operational Rollout Checklist

- [ ] Run a full dry run and review migration plan/report output.
- [ ] Back up critical Drive folders before first execute run.
- [ ] Execute migration on a small subset first.
- [ ] Execute full migration after verification.
- [ ] Export and archive JSON/Markdown reports for traceability.

## Website-in-Test / UI Surface

Current release is CLI-first and does not yet include a deployed web dashboard.
When the UI surface is added, publish a Vercel preview URL in `README.md`.
