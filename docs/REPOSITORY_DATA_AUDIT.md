# Git secret and customer-data audit

Audit date: 12 August 2026

## Result

No production secret or customer record was found in the tracked working tree
or complete Git history.

The audit covered:

- high-confidence API key, access-token, private-key and credential-bearing URL
  signatures across every Git revision;
- a broad `detect-secrets` scan of the tracked tree;
- email-address and phone-number candidates in tracked text;
- tracked and historical filenames for environment files, databases, SQL
  dumps, backups, keys, media, uploads and exports;
- the project requirements document; and
- ignored local files that could hold development or customer data.

## Reviewed matches

- `backend/.env.example` contains documented placeholders only, including the
  literal `user:password@host` example.
- CI and Docker Compose contain isolated development/test credentials only.
- Automated tests use reserved `example.com` addresses, invented names and
  synthetic phone ranges.
- Branch phone and WhatsApp numbers are approved public business contacts, not
  customer records.
- The README contains the intentionally published lead developer contact.
- The PRD contains no email address; number-like layout text did not represent
  customer phone records.

Local `backend/.env`, SQLite databases, media, logs, Next build output and
dependencies are ignored and are not tracked.

## Prevention

- Gitleaks scans full history in GitHub Actions.
- `scripts/check_tracked_sensitive_files.py` fails CI if common credential,
  database, backup, upload, media or export files become tracked.
- `.gitignore` excludes local environments, keys, database snapshots, dumps,
  backups, uploads and exports while explicitly allowing `.env.example`
  templates.

Source review is still required before committing free-form fixtures,
screenshots, support logs or documents: automated scanners cannot prove that
arbitrary prose or images contain no personal data.

If real data is ever committed, deleting the file in a later commit is not
enough. Revoke exposed credentials, notify the project owner, preserve an
incident record, and rewrite Git history with coordinated repository access.
