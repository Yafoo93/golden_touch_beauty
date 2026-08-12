# Production transport and environment review

Review date: 12 August 2026

## Enforced by the backend

The production settings now refuse to start unless:

- `DJANGO_DEBUG` is false;
- `DJANGO_SECRET_KEY` is unique and at least 50 characters;
- `DJANGO_ALLOWED_HOSTS` contains explicit non-local hostnames and no wildcard;
- `FRONTEND_URL` is an HTTPS origin without a path;
- every CSRF trusted origin is HTTPS and includes `FRONTEND_URL`;
- the database engine is PostgreSQL.

Production also enforces HTTPS redirection, one-year HSTS with subdomains and
preload, secure session and CSRF cookies, HTTP-only session cookies, `Lax`
SameSite cookies, content-type sniffing protection, and denied framing.

Render terminates TLS at its proxy, so Django trusts
`X-Forwarded-Proto: https` through `SECURE_PROXY_SSL_HEADER`. Forwarded hostnames
are not trusted; `Host` must still match `DJANGO_ALLOWED_HOSTS`.

The browser normally talks to Django through the same-origin Next.js
`/backend-api/` rewrite. CORS is restricted to the single configured frontend
origin with credentials enabled. CSRF protection remains required for every
state-changing session-authenticated request.

## Required Render backend variables

```text
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<unique random value of at least 50 characters>
DJANGO_ALLOWED_HOSTS=golden-touch-beauty.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://golden-touch-frontend.onrender.com
FRONTEND_URL=https://golden-touch-frontend.onrender.com
DATABASE_URL=<Render PostgreSQL internal connection URL>
DJANGO_SECURE_HSTS_SECONDS=31536000
```

Add the custom backend hostname to `DJANGO_ALLOWED_HOSTS` and the custom
frontend origin to both `FRONTEND_URL` and `DJANGO_CSRF_TRUSTED_ORIGINS` when
custom domains are activated. Use comma-separated values only where multiple
hostnames or origins are genuinely required.

The frontend service requires:

```text
BACKEND_INTERNAL_URL=https://golden-touch-beauty.onrender.com
NEXT_PUBLIC_SITE_URL=https://golden-touch-frontend.onrender.com
```

Never expose `DJANGO_SECRET_KEY`, `DATABASE_URL`, email credentials, or payment
provider secret keys through `NEXT_PUBLIC_*` variables.

## Manual deployment verification

These checks require access to Render and the deployed browser response and
cannot be proven from the repository alone:

1. Confirm the backend and frontend Render URLs both show a valid HTTPS
   certificate and redirect `http://` to `https://`.
2. Compare the Render environment variables with the list above without
   copying secret values into tickets, screenshots, or Git.
3. In browser developer tools after login, confirm `sessionid` is `Secure`,
   `HttpOnly`, and `SameSite=Lax`; confirm `csrftoken` is `Secure` and
   `SameSite=Lax`.
4. Send a state-changing request without `X-CSRFToken` and confirm HTTP 403;
   repeat from an unapproved Origin and confirm it is rejected.
5. Request the backend with an unapproved `Host` header and confirm HTTP 400.
6. Confirm response headers include `Strict-Transport-Security`,
   `X-Content-Type-Options: nosniff`, and `X-Frame-Options: DENY`.

Do not enable HSTS preload for a custom parent domain until every subdomain is
permanently HTTPS-capable.
