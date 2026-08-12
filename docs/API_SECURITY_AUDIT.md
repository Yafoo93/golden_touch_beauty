# API permission and branch-restriction audit

Last reviewed: 12 August 2026

This document is the security matrix for the mounted `/api/v1/` API. The
automated route registry in `backend/core/test_api_security_policy.py` fails if
an API is added without an explicit, reviewed permission policy.

## Permission matrix

| API area | Anonymous | Customer | Assigned staff | Owner | Data scope |
| --- | --- | --- | --- | --- | --- |
| Health, client error reporting | Allowed | Allowed | Allowed | Allowed | No operational records |
| Registration, login, password reset, email verification, CSRF | Allowed | Allowed | Allowed | Allowed | Authentication workflow only |
| Published branches, services, products, content, gallery, testimonials | Read | Read | Read | Read | Published/active records only |
| Booking availability and pickup branch options | Read | Read | Read | Read | Active public options only |
| Account profile and overview | Denied | Own | Own account | Own account | Requesting user only |
| Addresses and consent | Denied | Own | Own account | Own account | Requesting user only |
| Cart, wishlist, checkout, orders, bookings, receipts, notifications | Denied | Own | Own customer records | Own customer records | Requesting customer only |
| Website content, gallery, testimonials management | Denied | Denied | Denied | Full | Owner only |
| Branch, service, product and category management | Denied | Denied | Denied | Full | Owner only |
| Management overview and bookings | Denied | Denied | Assigned roles | Full | Assigned branches only |
| Inventory and stock adjustment | Denied | Denied | Manager/stock manager | Full | Assigned branches only |
| Reports and exports | Denied | Denied | Manager | Full | Assigned branches only |
| POS workspace and sales | Denied | Denied | Manager/cashier | Full | Assigned branches only |
| POS correction/reversal | Denied | Denied | Authorized manager | Full | Assigned branches and audit history |

## Automated guarantees

The backend suite verifies all of the following:

- Every mounted `/api/v1/` view explicitly declares its permission classes.
- Every API view is classified as public, authenticated-customer, owner-only,
  or assigned-branch staff. An unclassified new route fails the test suite.
- No management, report, or POS route can be classified as public or as a
  customer-only route.
- Inactive/unassigned staff and explicit branch-access denials grant no access.
- Assignment roles are enforced independently of the `is_staff` flag.
- Assigned staff querysets contain only records for their branches.
- Staff cannot select, adjust, report on, sell from, or retrieve objects from
  another branch.
- Owners retain global access, including cross-branch reporting.
- Customers cannot retrieve another customer's booking, order, receipt/payment,
  address, notification, cart item, profile information, or account totals.
- Operational booking, order, stock, payment, POS, receipt, and report records
  require protected branch attribution.
- Public APIs expose only published/active data and omit internal manager fields.

Run the complete automated audit from `backend`:

```powershell
python manage.py test --settings=config.settings.test
```

Run only the route-wide policy gate:

```powershell
python manage.py test core.test_api_security_policy --settings=config.settings.test
```

## Manual production checks still required

These checks depend on Render, real browser cookies, or production staff data;
they cannot be proven completely by an isolated automated test database.

1. In a private browser window, confirm a logged-out visit to `/account`,
   `/management`, and `/pos` redirects to `/login` and that their API requests
   return `401` or `403`.
2. Use two different browser profiles. Sign in as two different customers and
   try changing booking, order, and receipt references in the address bar.
   Confirm the other customer's record returns the branded not-found state.
3. Create or use a Makola-only manager/cashier and a Tse Addo-only record.
   Confirm the staff member cannot select or retrieve Tse Addo data in booking,
   inventory, reports, POS sales, or exports.
4. Disable that staff assignment in management, sign out and back in, and
   confirm management/POS access is removed.
5. In production browser developer tools, confirm the session cookie is
   `HttpOnly` and `Secure`, state-changing requests carry the CSRF header, and
   requests from an untrusted origin are rejected.

Record the date, tester, production URL, accounts used, and pass/fail evidence
for these five checks before launch. Never place real passwords in the record.

## Rate limits

| Scope | Limit | Applies to |
| --- | --- | --- |
| `auth-register` | 5/hour | Account registration |
| `auth-login` | 10/minute | Login attempts, keyed by client address while anonymous |
| `auth-reset` | 5/hour | Password-reset request and confirmation |
| `auth-verify` | 5/hour | Verification resend and confirmation |
| `payment-customer` | 10/minute | Customer booking and checkout mutations, shared per user |
| `payment-pos` | 30/minute | POS sale creation and authorized correction, shared per staff user |

Automated tests verify the limit boundary, `429` response shape, client/user
isolation, shared payment scopes, and exclusion of safe read requests.

Before launch, manually repeat the login limit against the production URL and
confirm separate public clients are not incorrectly grouped under Render's proxy
address. If the backend is ever scaled to multiple workers or instances, configure
a shared Django cache (for example Redis) first; an in-process cache cannot enforce
one counter across independent processes.
