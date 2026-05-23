# Security Policy

## Supported Versions

Security fixes are applied on the latest active branch.

## Reporting a Vulnerability

If you discover a security issue:

1. Do not open a public issue with exploit details.
2. Report privately to repository maintainers with:
   - issue summary
   - impact
   - reproduction steps
   - recommended mitigation (if available)

Maintainers will acknowledge receipt, validate impact, and coordinate remediation.

## Security Practices in This Repository

- OAuth token encryption at rest using Fernet.
- Sensitive files are excluded from git (`credentials.json`, token artifacts, key files).
- Dry-run default mode reduces accidental destructive operations.
- Explicit retry/backoff behavior for API reliability.

## User Security Recommendations

- Store credentials and token files with owner-only permissions.
- Rotate Google OAuth client credentials if compromise is suspected.
- Run migrations in dry-run mode before any execute run.
