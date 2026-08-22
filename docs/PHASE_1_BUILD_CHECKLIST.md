# Phase 1 Build Checklist — Plain-Language Version

This is the practical build order for Phase 1. It explains exactly which pages, APIs, database records, and administrator tools are created at each stage.

The [Development Roadmap](DEVELOPMENT_ROADMAP.md) remains the detailed engineering checklist. This document is the easier day-to-day production guide.

## What Phase 1 will deliver

At the end of Phase 1:

- Customers can visit the website, view services and products, register, log in, book services at Makola or Tse Addo, pay, shop, and track their activity.
- Administrators can manage branches, customers, services, products, bookings, payments, orders, stock, POS sales, and essential reports.
- Cashiers can sell products and services through the online POS.
- The owner can view the whole business and compare branches.
- Branch users can access only their assigned branches.

## Main website areas

| Area | Example routes | Who uses it? |
| --- | --- | --- |
| Public website | `/`, `/services`, `/shop`, `/contact` | Everyone |
| Authentication | `/login`, `/register`, `/forgot-password` | Customers and staff |
| Booking | `/book` and its four steps | Customers and reception staff |
| Customer dashboard | `/account`, `/account/appointments`, `/account/orders` | Logged-in customers |
| Management dashboard | `/management` and its subpages | Owner and authorized staff |
| POS | `/pos` | Cashiers and authorized managers |
| Django system admin | Backend `/admin/` | Technical/super administrators only |

The customer-facing management interface should use `/management`. Django's built-in `/admin/` remains a technical fallback and data-administration tool; it should not become the main daily dashboard.

---

## Stage 0 — Confirm the information we need

No customer page is built in this stage. We collect the real business information that will populate the pages.

### Business tasks

- [x] Record Makola address, phone/WhatsApp, map, opening days, and hours; email remains outstanding.
- [x] Record Tse Addo address, phone/WhatsApp, opening days, and hours; email and map remain outstanding.
- [x] Confirm the development service categories.
- [x] Draft development service names, descriptions, placeholder prices/durations, images, and initial branch availability.
- [x] Confirm that services require full payment, payable online or at clinic; Pay at Clinic follows the PRD pending-confirmation workflow.
- [x] Confirm the development product categories.
- [x] Draft development product names, descriptions, SKUs, variants, placeholder prices/costs, images, and opening branch stock.
- [x] Select Korapay as the intended payment provider, subject to merchant capability and integration verification.
- [ ] Confirm delivery, pickup, cancellation, refund, privacy, and terms policies.
- [x] Confirm development images may be used during development and will be reviewed/replaced for production.

### Result

The development catalogue is recorded in [BUSINESS_SEED_DATA.md](BUSINESS_SEED_DATA.md), and provisional policy copy is recorded in [DRAFT_POLICIES.md](DRAFT_POLICIES.md). Outstanding production information remains clearly marked. No placeholder naira or Lagos details will reach production; unverified ratings and statistics must be removed or replaced before launch.

---

## Stage 1 — Make the project easy to run and test

This stage prepares the development environment. Customers will not see a finished page yet.

### Development tasks

- [x] Create separate Django development, test, and production settings.
- [x] Add a local PostgreSQL Compose configuration.
- [x] Add GitHub CI for backend tests and frontend checks.
- [x] Add frontend-to-backend same-origin API rewriting.
- [x] Add the first branch, audit-log, and idempotency foundations.
- [x] Confirm PostgreSQL starts locally.
- [x] Apply all migrations to the development database.
- [x] Create the first owner/super-administrator account.
- [x] Create and run an idempotent development seed command for Makola, Tse Addo, test services, test products, branch availability, and opening stock.
- [x] Add consistent API error responses and a shared frontend error parser.
- [x] Add structured application logging, request correlation IDs, safe API error references, Next.js error boundaries, and browser error reporting.

### Result

A developer can start the database, Django, and Next.js; open the website; and confirm that the frontend can reach the backend.

---

## Stage 2 — Build the common website layout

This stage creates the visual parts used on every public page.

### Pages and components to create

- [x] Global header with logo, Home, Services, Shop, Book Now, Cart, and Login/Account.
- [x] Mobile navigation menu with accessible open/close control, active states, Escape handling, and links to Home, Services, Shop, Cart, Login/Account, and Book Now.
- [x] Global footer with Makola and Tse Addo contacts and hours, verified map availability, draft policy links, and confirmed WhatsApp social links.
- [x] Reusable gold, black, and outline button/link components with sizes, full-width, disabled, loading, focus, and reduced-motion states.
- [x] Reusable responsive service and product cards with images, categories, descriptions, Ghana cedi prices, business-specific metadata, stock/availability states, badges, and real navigation actions.
- [x] Reusable accessible form fields, text areas, field and summary validation messages, inline/panel loading indicators, and configurable empty states.
- [x] Reusable responsive page hero with eyebrow, main/accent title, description, optional optimized background image and overlay, alignment/size variants, and action area.
- [x] Shared cart item-count state and responsive header indicators with exact accessible counts, zero-state hiding, non-negative updates, and a `99+` visual cap.
- [x] Branded 404 page with a clear explanation and recovery links to Home, Services, and Shop.
- [x] General and root-level error pages with retry and automatic browser error reporting.
- [x] Global route-loading screen plus reusable primitive, card, list, and full-page skeleton components with accessible status and reduced-motion behavior.

### Routes affected

- Every frontend route through `frontend/src/app/layout.tsx`.

### Result

Every later page automatically has the correct responsive Golden Touch header, footer, colors, typography, buttons, and mobile behavior.

---

## Stage 3 — Build branches and branch access

Branching is part of Phase 1 and must exist before bookings, stock, sales, and reports.

### Customer pages/components

- [x] Branch selector used during booking, loaded from active PostgreSQL branch records and preserved in the booking URL.
- [x] Pickup-branch selector used during checkout with backend validation that every requested variant quantity is covered by unreserved, available branch stock.
- [x] Contact page showing Makola and Tse Addo together from PostgreSQL, with branch-specific address, hours, telephone, WhatsApp, email when available, and verified map state.

### Management pages

- [x] `/management/branches` — list branches through an owner-only API, including active state, contacts, hours, and assigned manager.
- [x] `/management/branches/new` — create a branch.
- [x] `/management/branches/[id]` — view and edit branch contacts, map, hours, manager, and active status.

### Backend work

- [x] Create the initial `Branch` database model.
- [x] Create public read-only active branch list/detail APIs with internal fields excluded.
- [x] Create owner-only branch create/update APIs.
- [x] Create staff-to-branch assignment records.
- [x] Create reusable permissions that restrict staff to assigned branches.
- [x] Require branch attribution on bookings, orders, stock, payments, POS sales, receipts, and reports.

### Result

The owner can manage Makola and Tse Addo. Later features cannot save a transaction without knowing its branch. A Makola-only employee cannot access Tse Addo records.

---

## Stage 4 — Create registration, login, and password pages

This is where the login and registration pages are built.

### Customer-facing pages

- [x] `/register` — full name, email, phone number, password, confirm password, terms/privacy agreement, and optional marketing consent.
- [x] `/login` — email or phone number plus password.
- [x] `/forgot-password` — request a password-reset email.
- [x] `/reset-password/[token]` — choose a new password.
- [x] `/verify-email` — explain that verification is required and allow resend.
- [x] `/verify-email/[token]` — process the verification link.
- [x] `/logout` action — invalidate the server session and return to the home page.

### Staff login

- [x] Staff use the same `/login` page.
- [x] After login, customers go to `/account`.
- [x] Authorized staff go to `/management` or `/pos` based on their active branch roles and permission overrides.

### Backend APIs

- [x] `GET /api/v1/auth/csrf/` — set/read the CSRF token required for secure form submission.
- [x] `POST /api/v1/auth/register/` — create a customer account.
- [x] `POST /api/v1/auth/login/` — authenticate by email or phone and create a secure session.
- [x] `POST /api/v1/auth/logout/` — destroy the session.
- [x] `GET /api/v1/auth/me/` — return the currently logged-in user and permissions.
- [x] `POST /api/v1/auth/verify-email/` — verify an email token.
- [x] `POST /api/v1/auth/resend-verification/` — resend verification.
- [x] `POST /api/v1/auth/password-reset/` — send reset instructions.
- [x] `POST /api/v1/auth/password-reset/confirm/` — set the new password.

### Security behavior

- [x] Use database-backed Django sessions with HTTP-only, SameSite cookies and Secure transport enforcement in production.
- [x] Do not save authentication, session, CSRF, reset, or verification tokens in `localStorage` or `sessionStorage`; enforce this with a frontend security check.
- [x] Require CSRF cookie/header validation centrally for login, registration, logout, and all unsafe browser API requests.
- [x] Normalize phone numbers to international format.
- [x] Rate-limit repeated login, registration, verification, and reset attempts.
- [x] Prevent users from discovering whether an email exists through password-reset responses.
- [x] Record important authentication events in the audit log.

### Tests

- [x] Register successfully with valid information.
- [x] Reject duplicate email or phone number.
- [x] Reject weak or mismatched passwords.
- [x] Log in using email.
- [x] Log in using phone number.
- [x] Reject invalid credentials.
- [x] Reset a forgotten password.
- [x] Prevent an inactive account from logging in.
- [x] Confirm customers cannot open management pages.

### Result

A new customer can register, verify the account, log in with email or phone, log out, and reset a forgotten password. The navigation changes from “Login” to the customer’s account control.

---

## Stage 5 — Build the public home and information pages

### Public pages

- [x] `/` — home page.
- [x] `/about` — company story and values.
- [x] `/contact` — both branches, maps, contacts, hours, and WhatsApp buttons.
- [x] `/gallery` — approved beauty-work images.
- [x] `/bridal-packages` — placeholder package structure complete; replace with approved packages before launch.
- [x] `/testimonials` — development samples and future video-transcript structure complete; replace with approved testimony before launch.
- [x] `/blog` — beauty tips list.
- [x] `/blog/[slug]` — individual beauty article.
  [x] `/faq` — frequently asked questions.
- [x] `/terms` — development-draft terms and conditions; replace with legal-approved copy before launch.
- [x] `/privacy` — development-draft privacy policy; replace with legal-approved copy before launch.
- [x] `/cancellation-refunds` — development-draft booking cancellation and refund policy; finalize operational rules and legal copy before launch.
- [x] `/delivery-returns` — development-draft product delivery and return policy; finalize operational rules and legal copy before launch.

### Home-page sections

- [x] Hero using an approved image from `frontend/public/images`.
- [x] Featured services loaded from the backend.
- [x] Featured products loaded from the backend.
- [x] Verified business statistics, or hide the section until verified.
- [x] Golden Touch difference/benefits.
- [x] Approved testimonials, or hide the section until supplied.
- [x] Book Appointment and Shop Products calls to action.

### Management pages

- [x] `/management/content` — edit approved operational website content.
- [x] `/management/gallery` — manage gallery items.
- [x] `/management/testimonials` — approve/hide testimonials.

### Result

A visitor can understand the business, see accurate Ghana branch information, and navigate to services, products, booking, or registration on desktop and mobile.

---

## Stage 6 — Build service management and public service pages

### Public pages

- [x] `/services` — published services with category filters and search.
- [x] `/services/[slug]` — service description, image, price/pricing note, duration, available branches, and Book This Service action.

### Management pages

- [x] `/management/services` — list services and publication state.
- [x] `/management/services/new` — create a service.
- [x] `/management/services/[id]` — edit service details, pricing, duration, images, branch availability, and booking eligibility.
- [x] `/management/service-categories` — manage service categories.

### Database/backend work

- [x] Create the initial `ServiceCategory` model and seed categories.
- [x] Create the initial `Service` model and seed services.
- [x] Create service price options for fixed, starting, range, option-based, or quoted prices.
- [x] Default non-consultation services to starting-from pricing and hold invoicing until management confirms the final treatment price.
- [x] Route contact-for-price service enquiries to the selected branch's official WhatsApp instead of direct booking.
- [x] Support one management-approved before/after result pair on each service detail page; link it to the customer's live signup/account photograph-advertising consent and keep source files in private media storage.
- [x] Create and seed service-to-branch availability for Makola and Tse Addo.
- [x] Add draft, published, and inactive states.
- [x] Add public service list/detail APIs.
- [x] Add authorized management create/update APIs.

### Result

Administrators can publish real services without changing code. Visitors can filter services, view accurate details, see eligible branches, and begin a booking.

---

## Stage 7 — Build product management and public shop pages

### Public pages

- [x] `/shop` — search, category filters, availability, and product cards.
- [x] `/shop/[slug]` — product images, description, variants, price, availability, quantity, favorite, and Add to Cart.
- [x] `/wishlist` — authenticated customer’s saved products with a synchronized global star-count badge.

### Management pages

- [x] `/management/products` — list products and stock summary.
- [x] `/management/products/new` — create a product.
- [x] `/management/products/[id]` — edit product, variants, SKU, prices, images, branches, and publication state.
- [x] Allow products to use contact-for-price WhatsApp enquiries and prevent those products from entering the cart.
- [x] Allow explicitly enabled pre-order variants with an estimated date, full-payment checkout, and no premature stock deduction.
- [x] `/management/product-categories` — manage product categories.
- [x] `/management/inventory` — view stock by branch.
- [x] `/management/inventory/[variant-id]` — view stock movement history.

### Database/backend work

- [x] Create and seed initial product category, product, variant, and image-path records.
- [x] Create and seed separate Makola and Tse Addo inventory balances.
- [x] Create append-only stock movements.
- [x] Add public product list/detail APIs.
- [x] Add management product and stock APIs.
- [x] Prevent stock from becoming negative.

### Result

Administrators can publish products and maintain separate Makola and Tse Addo stock. Customers can browse real products and choose a valid variant.

---

## Stage 8 — Build the shopping cart

### Customer pages

- [x] `/cart` — items, variant, quantity, unit price, subtotal, remove, and Continue to Checkout.
- [x] Cart drawer/preview opened from the header icon.

### Behavior

- [x] Cart access requires customer login; guest cart actions route to `/login`.
- [x] Customer cart contents are stored on the server and survive page refresh.
- [x] Prices and stock are checked again whenever the cart changes.
- [x] Customers cannot add more than available stock.

### Backend APIs

- [x] Get current cart.
- [x] Add cart item.
- [x] Change quantity.
- [x] Remove item.

### Result

A customer can build a valid cart and see the correct total without placing an order yet.

---

## Stage 9 — Build the four-step service-booking flow

The screenshots show four steps, but the behavior must follow the PRD.

### Booking pages

Use `/book` with the current step represented in the URL or query string so refresh/back navigation does not lose progress.

#### Step 1: Services and branch

- [x] Select one or more services.
- [x] Select Makola or Tse Addo.
- [x] Show only services available at the selected branch.
- [x] Show the separate duration and price of every selected service.

#### Step 2: Preferred date and time

- [x] Select a date.
- [x] Select a preferred time in 30-minute intervals.
- [x] Exclude blocked branch periods.
- [x] Explain that management may approve or propose another time.
- [x] Warn management if the appointment may finish after closing.

#### Step 3: Recipient and treatment information

- [x] Use the logged-in customer’s saved contact information.
- [x] Allow booking for the customer or another person.
- [x] Capture recipient name/contact when different.
- [x] Capture relevant allergies, conditions, previous treatments, and notes securely.
- [x] Capture optional photograph and marketing consent separately.

#### Step 4: Payment and confirmation

- [x] Show branch, services, date, time, recipient, item prices, total, payment requirement, and policies.
- [x] Allow the payment methods approved for those services.
- [x] Allow Pay at Clinic only when permitted.
- [x] Create the booking exactly once.
- [x] Display the booking reference and next steps.

### Backend work

- [x] Create Appointment, AppointmentServiceItem, and AppointmentHistory records.
- [x] Create booking blocks for holidays, meetings, events, or unavailable periods.
- [x] Implement Pending, Confirmed, Checked in, In progress, Completed, Cancelled, Rescheduled, and No-show statuses.
- [x] Block duplicate active bookings for the same customer and service.
- [x] Require an audited reason for an authorized duplicate override.
- [x] Allow management to approve, reject, cancel, or propose another time.
- [x] Require customer acceptance of a proposed time before confirmation.

### Management pages

- [x] `/management/bookings` — booking calendar/list with branch and status filters.
- [x] `/management/bookings/[reference]` — services, customer, payment, history, and available actions.
- [x] `/management/booking-blocks` — block branch dates/times.
- [x] `/management/bookings/new` — create a phone, WhatsApp, or walk-in booking.

### Result

A customer can book multiple services at a selected branch, request a preferred time, choose an allowed payment option, and receive a reference. Management can safely approve or change the request.

---

## Stage 10 — Build checkout and order creation

### Customer pages

- [x] `/checkout` — address, fulfillment, branch, order summary, and payment.
- [x] `/checkout/success` — order number, payment state, receipt, and next steps.
- [x] `/checkout/failed` — explanation and safe retry action.

### Checkout behavior

- [x] Require login before the final order is placed.
- [x] Select clinic pickup or delivery according to the approved policy.
- [x] For pickup, show only branches with sufficient stock.
- [x] For delivery, select or calculate a valid fulfillment branch internally.
- [x] Reserve stock for 30 minutes.
- [x] Release stock after timeout, failed payment, or cancellation.
- [x] Convert the reservation to a deduction only after successful payment.
- [x] Store an immutable snapshot of product names, variants, quantities, and prices.

### Backend work

- [x] Create Order and OrderItem records.
- [x] Create StockReservation records.
- [x] Implement Awaiting payment, Payment under review, Paid, Processing, Ready for pickup, Shipped, Delivered, Cancelled, Returned, and Refunded statuses.
- [x] Prevent overselling when two customers buy the last unit simultaneously.

### Result

A valid cart becomes one traceable order without overselling or losing stock.

---

## Stage 11 — Integrate payments

This stage connects both appointment booking and product checkout to real payments.

### Customer payment interfaces

- [ ] Provider-hosted card/Mobile Money checkout.
- [ ] Bank-transfer instructions and proof upload if approved.
- [ ] Pay at Clinic option for eligible appointments.
- [ ] Payment-pending, success, failed, cancelled, and retry states.

### Important security rule

- [ ] Do not build ordinary inputs for raw card number, CVV, or expiry date.
- [ ] Use the payment provider’s hosted page or secure embedded component.

### Backend work

- [ ] Create Payment and PaymentAllocation records.
- [ ] Create payment attempts with internal and gateway references.
- [ ] Create payment through a provider adapter rather than provider-specific booking/order code.
- [ ] Verify signed gateway webhooks.
- [ ] Make webhook processing idempotent so repeated events do not charge, confirm, or deduct stock twice.
- [ ] Confirm the payment amount, currency, reference, and customer before updating records.
- [ ] Reconcile payments against bookings, orders, and POS sales.
- [ ] Implement refund and reversal records.

### Management pages

- [ ] `/management/payments` — payments, methods, status, branch, date, and amount.
- [ ] `/management/payments/[reference]` — gateway events, allocation, receipt, and reconciliation details.
- [ ] `/management/bank-transfers` — review uploaded proof when applicable.

### Result

Successful payment confirms the correct booking/order exactly once. Failed or repeated callbacks cannot corrupt stock or transaction totals.

---

## Stage 12 — Build receipts and notifications

### Customer output

- [x] Booking confirmation page and email.
- [x] Order confirmation page and email.
- [x] Payment receipt page and email.
- [x] Printable/downloadable receipt.
- [x] Appointment change and cancellation messages.
- [x] Order-status messages.
- [x] In-system notification list.

### Pages

- [x] `/account/notifications` — customer notifications.
- [x] `/account/receipts/[reference]` — view/download a receipt.

### Backend work

- [x] Create Notification, Receipt, and Invoice records.
- [x] Send emails through background jobs.
- [ ] Retry failed email delivery without repeating the underlying transaction.
- [x] Schedule appointment reminders 24 hours and 6 hours before attendance.
- [x] Add pre-filled WhatsApp actions for staff where required.

### Result

Customers receive clear evidence and updates for their bookings, orders, and payments.

---

## Stage 13 — Build the customer dashboard

### Customer pages

- [x] `/account` — overview with upcoming appointments, completed services, orders, balances, and recent activity.
- [x] `/account/appointments` — all appointments grouped/filterable by status.
- [x] `/account/appointments/[reference]` — appointment services, branch, time, payment, history, and permitted actions.
- [x] `/account/orders` — all product orders.
- [x] `/account/orders/[reference]` — items, payment, fulfillment, tracking, and receipt.
- [x] `/account/profile` — full name, email, phone, date of birth, and gender.
- [x] `/account/addresses` — saved billing/delivery addresses.
- [x] `/account/consent` — marketing and photograph-consent settings.
- [x] `/account/wishlist` — saved products.
- [x] `/account/notifications` — operational notifications.
- [x] When a customer opens a product or service, related products/services are suggested below it.

### Security tests

- [x] A customer cannot view another customer’s order by changing the URL.
- [x] A customer cannot view another customer’s booking, payment, receipt, address, or profile.

### Result

A logged-in customer can manage their relationship with Golden Touch from one place.

---

## Stage 14 — Build the management dashboard

### Management home

- [x] `/management` — owner/manager overview.

### Dashboard cards

- [x] Today’s appointments.
- [x] Pending booking requests.
- [x] Proposed changes awaiting customer acceptance.
- [x] Today’s sales.
- [x] Product revenue.
- [x] Service revenue.
- [x] Outstanding balances.
- [x] Pending online orders.
- [x] Low-stock products.

### Management navigation

- [x] Branches.
- [x] Services.
- [x] Products.
- [x] Inventory.
- [x] Bookings.
- [x] Customers.
- [x] Orders.
- [x] Payments.
- [x] POS.
- [x] Reports.
- [x] Staff access.
- [x] Audit log.

### Filters

- [x] Date range.
- [x] Branch.
- [x] Product category.
- [x] Service category.
- [x] Payment method.
- [x] Booking status.
- [x] Order status.

### Permission behavior

- [x] Owner sees all branches and branch comparisons.
- [x] Branch managers see assigned branches only.
- [x] Receptionists do not see cost prices, profit, or sensitive medical information.
- [x] Cashiers see permitted sales/POS information only.
- [x] Stock managers see inventory operations only where authorized.

### Result

Management can operate the launched website without asking a developer to edit routine services, products, stock, bookings, or orders.

---

## Stage 15 — Build the online POS

### POS pages

- [x] `/pos` — product/service search and current sale.
- [x] `/pos/sales` — permitted sale history.
- [x] `/pos/sales/[reference]` — completed sale and receipt.
- [x] `/pos/end-of-day` — cashier totals and payment-method summary.

### POS behavior

- [x] Require staff login and branch selection/assignment.
- [x] Add products, services, or both to one sale.
- [x] Select an existing customer or use a walk-in customer.
- [x] Accept cash, approved electronic payment, bank-transfer record, partial payment, or split payment.
- [x] Deduct stock from the POS branch.
- [x] Record cashier and branch on every sale and receipt.
- [x] Print the receipt.
- [x] Prevent editing a completed sale.
- [x] Require authorized reversal/refund, reason, and audit history for corrections.
- [x] Clearly block completion if connectivity is lost in Phase 1.

### Result

A cashier can sell products and services at either branch while stock and revenue remain consistent with online transactions.

---

## Stage 16 — Build reports and analytics

### Report pages

- [x] `/management/reports/sales` — branch-scoped online-order and POS revenue with date/source filters, daily totals, payment methods, and transaction detail.
- [x] `/management/reports/bookings` — branch-scoped booking volume, status, source, value, duration, daily trend, and booking detail.
- [x] `/management/reports/products` — branch-scoped online/POS product performance, units, revenue, and current stock health.
- [x] `/management/reports/services` — branch-scoped booking/POS service demand, revenue, completion, duration, and daily performance.
- [x] `/management/reports/inventory` — branch-scoped stock position, cost/retail valuation, stock health, and movement activity.
- [x] `/management/reports/payments` — branch-scoped online/POS payment reconciliation by status, method, provider, source, and date.
- [x] `/management/reports/branches` — cross-operational branch comparison for sales, bookings, products, services, payments, and stock health.

### Reports included in Phase 1

- [x] Daily, weekly, and monthly sales — selectable interval on the branch-scoped sales report with reconciled online/POS totals.
- [x] Product revenue and product gross profit — revenue minus immutable sale-time product cost snapshots, with COGS and gross-margin percentage.
- [x] Service revenue — fully paid, non-cancelled booking service prices plus completed POS service lines, reported by service, source, day, branch, and selected period.
- [x] Appointment volume, cancellation, and no-show — branch/date-filtered appointment totals with separate cancellation and no-show counts, rates, daily activity, status breakdown, and transaction detail.
- [x] Popular services and best-selling products — top-five rankings by service occurrences and product units sold across bookings, online orders, and POS, with revenue as the tie-breaker.
- [x] Payment-method totals — successful, attempted, refunded, online, POS, gross, and net amounts by method with failed and pending attempts excluded from collections.
- [x] Stock levels and movements — current branch stock, reservations, availability, reorder health, valuation, movement-type totals, net changes, and a dated append-only movement ledger.
- [x] Branch comparison — permission-scoped side-by-side sales share, booking outcomes, product revenue/profit, service revenue, collections, and current stock health for Makola and Tse Addo.
- [x] Online orders and POS sales — reconciled revenue, transaction counts, channel shares, average sale values, date trends, branch totals, payment methods, and transaction detail.

### Export

- [x] PDF — professionally branded landscape report with Golden Touch letterhead, logo, branch contacts/locations/hours, filters, executive summary, detailed tables, confidentiality notice, and page numbers.
- [x] Excel — genuine `.xlsx` workbook with branded summary, filter provenance, formatted audit sheets, frozen headers, and complete report data.
- [x] CSV — UTF-8 export with report provenance, filter context, summary metrics, and complete detailed tables.

### Accuracy requirement

- [x] Every dashboard number has a written formula — an in-system metric methodology register documents the management overview and all seven reports, including permission/filter scope, date basis, inclusions, exclusions, rates, averages, zero-denominator behavior, stock valuation, and revenue recognition.
- [x] Refunds, reversals, cancellations, pending payments, and date boundaries are handled consistently — revenue excludes refunded/reversed/cancelled transactions and pending payments; refund reports retain gross collection then subtract the correction; booking demand preserves cancellations while recognized service revenue excludes cancelled, rejected, and unpaid bookings; correction activity uses its correction date; report boundaries are inclusive local calendar dates with regression coverage at both edges.
- [x] Automated tests reconcile totals with raw transactions — independent ORM control totals validate sales, bookings, product units/revenue/COGS/profit, recognized service revenue, inventory balances/movements, payment gross/refunds/net, and branch totals; report summaries are also reconciled to their detailed ledgers.
- [x] Estimated operating result is labeled as an estimate because full service costing is not yet available — branch reports calculate product gross profit plus recognized service revenue, while the UI, metric methodology, and exported reports explicitly warn that service consumables, labour, commissions, delivery costs, rent, utilities, taxes, and other operating expenses are not yet deducted.

### Result

The owner can understand performance for the whole business and compare Makola with Tse Addo using trustworthy figures.

---

## Stage 17 — Security and production launch

### Security checks

- [x] Test every API permission and branch restriction.
- [x] Test that customers cannot access management endpoints.
- [x] Test file-upload type and size restrictions.
- [x] Test authentication and payment rate limits.
- [x] Run dependency and secret scans.
- [x] Review HTTPS, cookies, CSRF, CORS, trusted proxy, and production environment variables.
- [x] Verify that no secret or customer data is committed to Git.

### Quality checks

- [x] Test mobile, tablet, laptop, and desktop layouts.
- [ ] Test keyboard navigation and screen-reader labels.
- [ ] Test Chrome, Edge, Firefox, and Safari where available.
- [ ] Test slow network, failed requests, duplicate clicks, and browser refresh during checkout/booking.
- [ ] Test payment success, delay, failure, cancellation, duplicate webhook, and refund.
- [ ] Test concurrent purchase of the last product unit.

### Launch work

- [ ] Deploy staging.
- [ ] Load approved production branches, services, products, prices, and opening stock.
- [ ] Complete business user-acceptance testing.
- [ ] Train owner, managers, receptionists, cashiers, and stock users.
- [ ] Configure production domain and HTTPS.
- [ ] Configure production database, media storage, email, background workers, and payment credentials.
- [ ] Configure daily backups, monitoring, alerts, and error reporting.
- [ ] Test backup restoration.
- [ ] Perform a controlled soft launch.
- [ ] Obtain final business sign-off.

### Result

Phase 1 is live and customers can safely register, book and pay for services, purchase products, receive receipts, and manage their accounts across a properly controlled multi-branch system.

---

## Simple production sequence

Use this order during development:

1. Gather real business information.
2. Finish the development environment.
3. Build the shared header, footer, and design components.
4. Build branch management and branch permissions.
5. Build registration, login, verification, and password reset.
6. Build the home and information pages.
7. Build service management and service pages.
8. Build product management and shop pages.
9. Build the cart.
10. Build the service-booking wizard.
11. Build checkout and order creation.
12. Connect real payments.
13. Build receipts and notifications.
14. Build the customer dashboard.
15. Build the management dashboard.
16. Build the POS.
17. Build reports and analytics.
18. Test, deploy, train users, and launch.

## Where development should begin now

The next work should be:

- [ ] Complete Stage 0 business decisions that block database content and payment design.
- [ ] Finish the remaining Stage 1 environment tasks.
- [ ] Begin Stage 2 by building the responsive shared header, footer, design tokens, and reusable controls.
- [ ] Then complete Stage 3 branches before Stage 4 login and registration, because staff access and transaction scope depend on branches.

Login and registration are therefore created in **Stage 4**, after the shared layout and branch-access foundation, and before the public catalogue, booking, cart, checkout, payment, dashboard, and POS features.
