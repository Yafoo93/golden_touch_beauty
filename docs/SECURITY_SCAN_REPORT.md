# Dependency and Secret Scan Report

Scan date: 12 August 2026

## Scope

- Python production dependencies pinned in `backend/requirements.txt`.
- Frontend production and development dependencies in `frontend/package-lock.json`.
- Git-tracked files using `detect-secrets` detectors.
- Complete Git history using high-confidence credential and private-key signatures.
- Tracked filenames commonly used for private keys, credentials, and environment secrets.

## Dependency results

### Frontend

The first `npm audit` identified six high-severity advisories affecting Next.js and transitive packages. The remediation upgraded Next.js and `eslint-config-next` from 16.2.10 to 16.3.0 and refreshed affected transitive dependencies, including Sharp, PostCSS, Nano ID, JS YAML, and brace expansion.

Final command:

```powershell
cd frontend
npm.cmd audit --audit-level=high
```

Final result: **0 vulnerabilities**.

### Backend

Command:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
```

Final result: **No known vulnerabilities found**.

The upgraded frontend also completed a full Next.js 16.3.0 production build successfully. The repository's broader ESLint run still reports existing React purity/effect violations outside the dependency-remediation changes; these should be handled as a separate code-quality task and do not represent dependency or secret-scan findings.

## Secret-scan results

Commands and methods:

```powershell
.\backend\.venv\Scripts\detect-secrets.exe scan
```

The scanner's candidates were manually reviewed. They were limited to:

- CI-only PostgreSQL and Django values used in an isolated test job;
- an explicit `user:password@host` placeholder in `backend/.env.example`;
- local-only Docker Compose credentials;
- dummy passwords in automated tests;
- password field names and validation messages.

No production credential, API key, access token, private key, or customer secret was found in the tracked working tree.

A separate high-confidence scan across every Git revision found only the documented placeholder database URL in `backend/.env.example`. Tracked sensitive-filename review found only `backend/.env.example` and `frontend/.env.example`, both intentional templates. Real local environment files remain ignored by Git.

## Continuous enforcement

GitHub Actions now runs:

- Gitleaks against full Git history;
- `pip-audit` against backend requirements;
- `npm audit --audit-level=high` against the frontend lockfile.

Any future detected secret or high/critical dependency advisory will fail CI. Advisory databases change over time, so these checks must run on every push and pull request rather than being treated as a one-time guarantee.
