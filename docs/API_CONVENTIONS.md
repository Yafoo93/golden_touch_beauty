# API Conventions

## Versioning

Application endpoints use the `/api/v1/` prefix. API documentation remains available through `/api/schema/`, `/api/docs/`, and `/api/redoc/`.

## Public service catalogue

These read-only endpoints do not require authentication:

- `GET /api/v1/services/` lists published, active services available at an active branch.
- `GET /api/v1/services/{slug}/` returns a service’s full public details, branches, pricing, and structured price options.
- `GET /api/v1/services/categories/` lists categories that contain at least one public service.
- `GET /api/v1/services/featured/` lists up to six featured public services.

The service list accepts `category`, `search`, `ordering`, and `branch` query
parameters. `branch` is an active branch code and is used by booking to return
only services available at the selected location.

The booking branch selector reads from `GET /api/v1/branches/`, which exposes
only active public branches. Its selected branch code is preserved in the
`/book` query string; changing branches clears any earlier service selection so
services from one location cannot leak into another location's booking draft.
Supported ordering fields are `name`, `price`, `duration_minutes`, and
`category__name`; prefix a field with `-` for descending order. Draft,
inactive, branch-unavailable, and category-inactive services are excluded.
Internal publication flags and audit timestamps are never returned.

## Public product catalogue

These read-only endpoints do not require authentication:

- `GET /api/v1/products/` lists active, published products with an active
  variant, customer price, variant summary, and live availability state.
- `GET /api/v1/products/{slug}/` returns the public product description,
  images, active variants, selling prices, preorder information, and branches
  with live stock.
- `GET /api/v1/products/categories/` lists categories containing at least one
  public product.
- `GET /api/v1/products/featured/` lists featured public products.

The product list accepts `category`, `search`, `availability`, and `ordering`.
Availability may be `in_stock`, `preorder`, or `out_of_stock`. Search covers
product name, brand, description, and category. Cost prices, reserved
quantities, and raw branch stock counts are not exposed.

Authenticated customer wishlists use:

- `GET /api/v1/products/wishlist/` to list the signed-in customer’s saved
  public products.
- `POST /api/v1/products/wishlist/` with `product_slug` to save a product.
- `DELETE /api/v1/products/wishlist/{product_slug}/` to remove it.

Wishlist writes require the session CSRF token. Records are always scoped to
the authenticated customer and duplicate saves are idempotent. Product-card,
product-detail, header, mobile-navigation, and direct `/wishlist` guest actions
route to `/login` with a safe local return path.

Product management begins with:

- `GET /api/v1/products/management/` for an owner-only list of every product,
  including drafts and inactive records, active and total variant counts,
  selling-price range, aggregate on-hand/reserved/available quantities,
  low-stock balance count, and stock totals grouped by branch.
- `POST /api/v1/products/management/` creates a product, its initial SKU, and
  opening inventory for the selected active branches in one transaction.
- `GET /api/v1/products/management/category-options/` and
  `GET /api/v1/products/management/branch-options/` supply the active choices
  used by the create-product form.

Product creation requires the owner/super-administrator session and CSRF
protection, validates the uploaded image and unique SKU, and writes an immutable
audit event after success.

- `GET /api/v1/products/management/{id}/` returns the complete product,
  variants, pricing, reserved quantities, and branch inventory for editing.
- `PATCH /api/v1/products/management/{id}/` updates product content,
  publication, an optional replacement image, variants, SKUs, prices, and
  branch stock transactionally. Stock cannot be reduced below its reserved
  quantity, and successful updates are audited.
- `GET|POST /api/v1/products/management/product-categories/` lists or creates
  product categories.
- `GET|PATCH|DELETE /api/v1/products/management/product-categories/{id}/`
  retrieves, updates, or deletes an empty product category. Categories with
  products must be reassigned or deactivated instead of deleted. Category
  slugs remain stable when display names change.

## Inventory management

- `GET /api/v1/inventory/management/` returns variant stock by branch,
  including on-hand, reserved, available, reorder threshold, selling price,
  operational availability, and low-stock status.

Owners receive all branches. Assigned branch managers and stock managers only
receive inventory for their active branch assignments. Optional `branch`,
`search`, and `low_stock=true` query parameters filter the authorized result.

- `GET /api/v1/inventory/management/{variant-id}/` returns the current
  authorized branch balances and immutable movement history for one variant.
- `POST /api/v1/inventory/management/adjustments/` applies a signed stock
  adjustment to one variant at one authorized branch. The operation locks the
  balance row, prevents stock falling below reservations, and appends the
  reason, actor, delta, and resulting balance to movement history.

Movement entries record opening balances, adjustments, reservations, releases,
sales, returns, and transfers with quantity deltas, resulting balances,
references, actor, branch, and timestamp. Enabling the ledger creates an
explicit imported opening-balance entry for pre-existing inventory.

Stock movements are append-only. Existing entries reject instance updates,
queryset updates, bulk updates, instance deletion, and queryset deletion. The
admin also disables create, change, and delete operations; movements are only
created by approved inventory workflows.

Inventory balances are protected against negative on-hand, reserved, and
reorder quantities at both API-validation and database-constraint levels.
Reserved stock cannot exceed on-hand stock, and movement snapshots enforce the
same non-negative and reservation invariants.

## Customer cart

Cart access requires an authenticated customer session. Product-card,
product-detail, header, mobile-navigation, and direct `/cart` guest actions send
the visitor to `/login` with a safe local return path. Cart contents are stored
on the server rather than in guest browser storage.

Every cart mutation is sent to `POST /api/v1/products/cart/validate/`. The
endpoint reloads the current product and variant data, uses the current selling
price, and checks unreserved stock at active branches. A standard item is capped
at the highest quantity fulfillable by one branch; unavailable items are
removed. Pre-order variants are not capped by on-hand stock. The response
contains canonical `items` plus human-readable `adjustments`, and replaces the
customer's server cart. `GET /api/v1/products/cart/` returns the current server
cart. `POST /api/v1/products/cart/items/` adds a variant or increments its
existing quantity, then applies the same live price and stock validation before
returning the complete canonical cart.
`PATCH /api/v1/products/cart/items/{variant_id}/` sets an existing cart line's
quantity, rejects lines outside the signed-in customer's cart, and returns the
same canonical cart and adjustment format.
`DELETE /api/v1/products/cart/items/{variant_id}/` removes that customer-owned
line and returns the revalidated remaining cart. Missing lines and lines owned
by another customer return 404 without changing that other cart. All cart
endpoints require authentication, and all unsafe requests require CSRF
protection.

## Service catalogue management

These endpoints require the active owner/super-administrator session and CSRF
protection for unsafe requests:

- `POST /api/v1/services/management/` creates a service with pricing,
  publication state, branch assignments, booking behavior, and an image.
- `PATCH /api/v1/services/management/{id}/` partially updates a service.

Writes are validated transactionally. Branch assignments and structured price
options are synchronized as part of the same request, replaced images are
cleaned up after a successful update, and every successful create or update
produces an immutable audit event. Customers and anonymous callers receive a
permission error.

## Error response format

Every REST API failure returns JSON with one stable envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Some submitted information is invalid.",
    "status": 400,
    "details": {
      "email": ["This field is required."]
    }
  }
}
```

Fields:

- `code`: stable machine-readable value used by the frontend.
- `message`: safe summary suitable for displaying to a user.
- `status`: HTTP status code repeated for convenient client handling.
- `details`: field-level or exception-specific information; an empty object when no safe details are available.

Common codes include:

| HTTP status | Code | Meaning |
| ---: | --- | --- |
| 400 | `validation_error` | Submitted fields failed validation. |
| 400 | `invalid_json` | The request body is not valid JSON. |
| 401/403 | `not_authenticated` | A valid login session is required. |
| 403 | `permission_denied` | The user is logged in but lacks permission. |
| 404 | `not_found` | The resource or API endpoint does not exist. |
| 405 | `method_not_allowed` | The endpoint does not support that HTTP method. |
| 409 | `conflict` | The request conflicts with current resource state. |
| 415 | `unsupported_media_type` | The request content type is unsupported. |
| 422 | `business_rule_violation` | Valid fields violate an application business rule. |
| 429 | `rate_limited` | The caller exceeded a request limit. |
| 500 | `server_error` | An unexpected internal error occurred. |

Unexpected errors are logged on the server with diagnostic context, while the response hides exception messages and sensitive implementation details.

## Frontend handling

Use `apiFetch` from `frontend/src/lib/api.ts`. It includes browser session cookies and throws `ApiError` for non-successful responses:

```ts
try {
  const result = await apiFetch<Result>("example/");
} catch (error) {
  if (error instanceof ApiError) {
    console.log(error.code, error.message, error.details);
  }
}
```

Form pages should use `error.details` for field-level messages and `error.message` for the page-level alert. They should not implement separate parsing rules for individual endpoints.

## Booking endpoints

Customer endpoints use the authenticated Django session:

- `GET/POST /api/v1/bookings/`
- `GET /api/v1/bookings/availability/?branch={code}&date=YYYY-MM-DD&duration={minutes}`
- `GET /api/v1/bookings/{reference}/`
- `POST /api/v1/bookings/{reference}/proposal/`

Management endpoints are restricted to the owner or staff assigned to the
booking/block branch:

- `GET/POST /api/v1/bookings/management/all/`
- `GET /api/v1/bookings/management/options/`
- `GET /api/v1/bookings/management/{reference}/`
- `POST /api/v1/bookings/management/{reference}/action/`
- `GET/POST /api/v1/bookings/management/blocks/`

Booking creation requires a UUID `client_request_id`. Repeating a successful
request with the same request ID returns the existing booking rather than
creating a duplicate. The selected service names, options, prices, and
durations are snapshotted into booking service items.

## Checkout and order endpoints

All checkout and customer-order endpoints require an authenticated Django
session:

- `GET /api/v1/orders/checkout/options/`
- `POST /api/v1/orders/checkout/`
- `GET /api/v1/orders/`
- `GET /api/v1/orders/{reference}/`
- `POST /api/v1/orders/{reference}/cancel/`

Checkout receives a UUID `client_request_id`. The backend locks the customer
and selected branch inventory rows, rechecks live prices and available stock,
creates immutable order-item snapshots, and reserves stock for 30 minutes.
Repeating the same request ID returns the existing order.

Run `python manage.py release_expired_order_reservations` from a production
scheduler at least once per minute. It releases expired reservations, records
append-only stock movements, and marks their unpaid orders cancelled. Payment
failure/cancellation uses the same release service. Verified payment calls
`orders.services.capture_order_stock`, which atomically converts reservations
into final stock deductions and is safe to call repeatedly.
