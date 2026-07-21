# ADR-001: Same-origin Django session authentication

- Status: Accepted
- Date: 21 July 2026

## Context

Golden Touch uses a Next.js browser application and a Django REST API. The system handles customer contact data, treatment information, orders, payments, inventory, and staff permissions. Authentication must support customers, administrators, branch users, and browser-based POS sessions without exposing reusable credentials to JavaScript-accessible storage.

## Decision

Use Django's server-side session authentication with CSRF protection. In production, the browser will access the API through a same-origin path exposed by the Next.js/reverse-proxy layer. Session identifiers remain in secure, HTTP-only, SameSite cookies. The frontend will obtain and send Django CSRF tokens for unsafe requests.

Authorization remains exclusively server-side. Next.js route checks may improve navigation but never replace Django permissions or object-level branch checks.

## Consequences

- No access or refresh tokens are stored in `localStorage` or `sessionStorage`.
- Browser and POS requests use `credentials: "include"` where required.
- Login rotates the Django session key; logout invalidates the server session.
- Production requires HTTPS, secure cookies, trusted proxy configuration, and correct CSRF origins.
- Public APIs and future native mobile applications may later require a separately reviewed token/OAuth design; that is not part of this decision.
- Horizontal access and cross-branch authorization tests are mandatory.

## Rejected alternatives

- Browser-stored JWTs: rejected because XSS could expose reusable tokens.
- Custom refresh-token cookies: rejected for Phase 1 because Django sessions already provide revocation and rotation with less custom security code.
- Disabling CSRF for convenience: rejected because cookie-authenticated unsafe requests require CSRF protection.
