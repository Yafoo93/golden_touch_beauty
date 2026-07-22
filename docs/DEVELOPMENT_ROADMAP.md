# Golden Touch Beauty Centre — Development Roadmap

This checklist translates the Product Requirements Document (PRD) and approved UI reference into two production phases. It begins from the repository's current Django and Next.js foundations and ends with the wider operating platform described in the PRD. The PRD defines system behavior and always takes precedence where a screenshot differs; screenshots guide presentation and interaction styling only.

For a simpler explanation showing exactly which pages and backend features are built at each stage, use the [Phase 1 Plain-Language Build Checklist](PHASE_1_BUILD_CHECKLIST.md).

## Delivery strategy

### Phase 1 — Multi-branch commerce and booking launch

Deliver a production-ready multi-branch customer website where customers can discover services, select a branch, book and pay for appointments, buy products, select an eligible pickup branch, and manage their activity. Provide the owner and branch-authorized administrators with catalogue management, bookings and orders, branch analytics, payments, branch inventory, receipts, and a usable online POS.

### Phase 2 — Advanced business operations

Expand the launched multi-branch platform with staff roles and assignment, advanced appointment operations, home services, treatment records, deeper inventory operations, expenses/income analysis, offline POS synchronization, content governance, notifications, reporting, and audit controls.

> [!IMPORTANT]
> Multi-branch operation is a Phase 1 requirement. Every booking, order, payment, sale, inventory movement, POS device/session, expense, permission, report, and audit event must carry or derive the correct branch scope. The owner can view the whole business; branch-authorized users can access only assigned branches.

## Current baseline

- [x] PRD v1.0 is available.
- [x] Brand logos and initial service/product imagery are available.
- [x] Django 5.2 and Django REST Framework project is scaffolded.
- [x] PostgreSQL environment configuration is scaffolded.
- [x] Domain apps are scaffolded for accounts, services, products, bookings, orders, payments, inventory, POS, reports, notifications, expenses, branches, customers, and audit logging.
- [x] Custom UUID user model and email-or-phone authentication backend exist.
- [x] API schema, Swagger UI, ReDoc, and health endpoint are configured.
- [x] Next.js 16, React 19, TypeScript, Tailwind CSS, and ESLint are scaffolded.
- [x] Initial UI reference covers the home page, service catalogue, shop, booking wizard, authentication, and customer dashboard.
- [x] Architecture decision selects same-origin Django sessions with CSRF protection; tokens will not be stored in browser local storage.
- [ ] Backend dependencies and local PostgreSQL are verified on every developer machine.
- [ ] Frontend health check references an existing image filename and verified API URL.
- [ ] Automated CI, deployment environments, and production monitoring are configured.

## Decisions required before feature development

- [ ] Approve the two-phase scope and define the first public launch date.
- [ ] Complete the remaining Makola and Tse Addo information identified in `BUSINESS_SEED_DATA.md`; development contacts and hours are recorded, but branch emails and the Tse Addo map are outstanding.
- [x] Record development service names, drafted descriptions, placeholder prices/durations, images, branch availability, and payment eligibility.
- [x] Record development product names, categories, drafted descriptions, SKUs, variants, placeholder prices/costs, images, and opening quantities.
- [x] Select Korapay as the intended Phase 1 payment gateway, subject to merchant approval and verification of Ghana Mobile Money, cards, refunds, webhook quality, fees, settlement, and international-payment support.
- [ ] Confirm whether Phase 1 offers delivery, clinic pickup, or both.
- [ ] Confirm delivery pricing workflow and service areas.
- [ ] Confirm appointment deposit rules, cancellation policy, refund policy, and Pay at Clinic eligibility.
- [ ] Confirm production domain, email sender, hosting, object storage, database, and backup provider.
- [ ] Review every development image for ownership/licensing before production use; current images are approved only as replaceable development assets.
- [ ] Populate the implementation from the PRD's Ghana branch details and Ghana cedis (GHS/GH₵); treat all Nigeria details and naira symbols in the screenshots as non-authoritative placeholders.
- [ ] Remove demo-role shortcuts and fabricated statistics/testimonials from the production UI unless the business supplies verified values.

## Phase 1 — Commerce and booking launch

### 1. Engineering foundation

- [ ] Create `development`, `staging`, and `production` configuration profiles.
- [x] Add Docker Compose or equivalent local services for PostgreSQL and supporting dependencies.
- [x] Validate `python manage.py check`, migrations, and tests in the current development environment.
- [ ] Validate frontend lint and production build from a clean setup.
- [ ] Add formatting, linting, type checking, backend tests, frontend tests, and build checks to CI.
- [x] Add structured logging, request IDs, safe error handling/reporting, and a database-aware health endpoint; deployment readiness checks remain part of staging.
- [ ] Configure environment validation so missing variables fail with useful messages.
- [ ] Configure media/file storage abstraction for local development and S3-compatible production storage.
- [ ] Complete API pagination, filter, and naming conventions; `/api/v1/` versioning and the consistent error format are implemented.
- [x] Create and run an idempotent seed command for Makola, Tse Addo, services, products, branch availability, variants, and opening stock; the owner account is managed separately.
- [ ] Add a shared money representation using integer minor units or a fixed decimal type; never use floating-point values for money.
- [ ] Add a reference-number strategy for bookings, orders, payments, receipts, and POS sales.
- [ ] Create a test-data policy that prevents demo data from reaching production.

**Foundation exit gate**

- [ ] A new developer can launch the frontend, backend, and database by following the README.
- [ ] CI passes from a clean clone.
- [ ] No secrets, local databases, generated uploads, or caches are tracked by Git.

### 2. Multi-branch foundation and management

- [ ] Complete branch API and reusable branch permissions; the branch model, migrations, seed data, validation, and Django Admin management are in place.
- [x] Seed Makola and Tse Addo using the currently supplied development details.
- [x] Add staff-to-branch membership with one or more roles and individual permission overrides.
- [ ] Implement owner-wide access and branch-scoped access policies once, then reuse them across every domain.
- [ ] Add branch selection to service booking and eligible pickup branch selection to checkout.
- [ ] Enable/disable services per branch.
- [ ] Maintain product selling prices consistently across branches while tracking inventory separately.
- [ ] Attribute every booking, order, payment, POS sale, stock movement, expense, staff action, receipt, reversal, and audit event to a branch. *(Phase 1 transaction foundations now require branches for bookings, orders, stock, payments, POS sales, receipts, and persisted report snapshots; remaining Phase 2 records stay pending.)*
- [ ] Add branch filters to admin lists, analytics, reports, and exports.
- [ ] Prevent cross-branch object access in the API, including guessed UUIDs.
- [ ] Test owner-wide access, multi-branch assignments, single-branch restrictions, inactive branches, and cross-branch denial.

### 3. Design system and application shell

- [ ] Convert the screenshots into documented design tokens: black/charcoal surfaces, gold accents, cream headings, muted text, borders, radii, spacing, shadows, and interaction states.
- [ ] Select and license the heading and body fonts or choose production-safe alternatives.
- [ ] Build responsive header, navigation, mobile menu, cart indicator, account control, and footer components.
- [ ] Build reusable buttons, links, cards, badges, form controls, dialogs, alerts, loaders, skeletons, empty states, and pagination.
- [ ] Add accessible focus states, keyboard navigation, form labels, error summaries, and contrast checks.
- [ ] Create responsive breakpoints and verify phone, tablet, laptop, and wide-desktop layouts.
- [ ] Define image aspect ratios, responsive sizes, compression rules, and meaningful alternative text.
- [ ] Use `next/image` and map the downloaded assets in `frontend/public/images` to approved services/products.
- [ ] Add 404, error, maintenance, loading, and offline-state screens.
- [ ] Add metadata, Open Graph cards, sitemap, robots configuration, canonical URLs, and structured data where relevant.

**UI reference mapping**

- Home: hero, metrics, featured services, differentiators, featured products, testimonials, call to action, and footer.
- Services: hero, category filters, responsive service cards, detail links, and booking actions.
- Shop: hero, search, category filters, product grid, favorites, and cart actions.
- Booking: four-step service, date/time, customer-details, and payment workflow.
- Account: sign-in, registration, overview, appointments, orders, and profile.
- Admin/POS: create a matching operational design system optimized for speed and clarity; these screens are not fully represented in the supplied references.

### 4. Accounts, authentication, and customer profiles

- [ ] Normalize and validate Ghanaian/international phone numbers.
- [ ] Decide whether email and phone are both required or whether either can be optional while remaining a login identifier.
- [ ] Add registration API and UI with full name, email, phone, password, confirmation, and consent fields.
- [ ] Add login with email or phone plus password.
- [ ] Add secure logout, session/token refresh strategy, and session expiration.
- [ ] Add email verification and resend flow.
- [ ] Add forgot-password and secure password-reset flow.
- [ ] Add login throttling, lockout/rate limits, and audit events.
- [ ] Add customer profile read/update and saved delivery addresses.
- [ ] Add consent capture for terms, privacy, and marketing.
- [ ] Add account navigation and protected-route handling in Next.js.
- [ ] Add admin account management without exposing password hashes or sensitive treatment information.
- [ ] Test registration, duplicate identities, login by both identifiers, inactive accounts, logout, and reset flows.

### 5. Service catalogue and content

- [ ] Model service categories, services, price type, price/options, duration, images, publication state, booking eligibility, and display order.
- [ ] Add branch availability and per-branch active status to services.
- [ ] Add service list/detail APIs with category, search, ordering, and published-only filters.
- [ ] Build admin CRUD for service categories, services, pricing, duration, images, and active status.
- [ ] Build the public service catalogue and responsive service-detail pages.
- [ ] Add featured-service controls for the home page.
- [ ] Add management validation preventing incomplete services from being published.
- [ ] Seed approved catalogue data and map images from `frontend/public/images`.
- [ ] Add service SEO metadata and shareable URLs.
- [ ] Test draft visibility, price rendering, filters, ordering, and unavailable services.

### 6. Product catalogue and stock baseline

- [ ] Model product categories, products, variants, images, SKU, selling price, cost price, published status, featured status, preorder flag, and estimated availability date.
- [ ] Model inventory balances and reservations separately for every branch.
- [ ] Add public product list/detail APIs with search, category, price, availability, and ordering filters.
- [ ] Build admin CRUD for products, variants, images, prices, stock, reorder level, and publication status.
- [ ] Build the shop page, product details, search, category filters, stock messaging, featured products, and related products.
- [ ] Implement wishlist for authenticated customers.
- [ ] Prevent purchase of unpublished or unavailable variants unless preorder is enabled.
- [ ] Seed the approved product catalogue and map approved product images.
- [ ] Test variant pricing, stock status, draft visibility, search, filters, and preorder presentation.

### 7. Cart and checkout

- [ ] Implement persistent guest cart and authenticated cart.
- [ ] Merge the guest cart safely after login.
- [ ] Support variant selection, quantity updates, removal, and cart totals.
- [ ] Revalidate price and availability on every cart mutation and at checkout.
- [ ] Implement a 30-minute stock reservation with an explicit expiration timestamp.
- [ ] Release reservations after expiration, failed payment, cancellation, or abandoned checkout.
- [ ] Prevent overselling through transactional database locking/constraints.
- [ ] Capture billing address, delivery address, fulfillment method, and customer notes.
- [ ] Support clinic pickup and/or manual delivery quotation according to the approved Phase 1 decision.
- [ ] Display an order summary with item snapshots, quantities, unit prices, subtotal, delivery, discounts if applicable, and total.
- [ ] Create orders with immutable item and pricing snapshots.
- [ ] Test concurrent checkout, expired reservations, price changes, sold-out products, and duplicate submission.

### 8. Appointment booking

- [ ] Model appointments, appointment service items, status history, customer/recipient details, preferred date/time, notes, price snapshots, and payment state.
- [ ] Require an eligible branch selection and retain it throughout booking changes and payment.
- [ ] Implement the PRD booking statuses and valid state transitions.
- [ ] Support one or more services under one booking reference; retain duration and price for each service item.
- [ ] Implement 30-minute booking intervals within configured opening hours.
- [ ] Implement booking-block records for closures and unavailable periods.
- [ ] Decide Phase 1 capacity behavior: simple slot capacity or management-approved requests. Do not imply staff-level availability before staffing is delivered.
- [ ] Warn management when a requested service may end after closing time.
- [ ] Block duplicate active bookings for the same customer and service.
- [ ] Allow authorized override only with an audit reason.
- [ ] Build the four-step booking UI from the supplied design.
- [ ] Require authentication before final booking confirmation while preserving the customer's in-progress selection.
- [ ] Add booking review, confirmation reference, receipt link, and failure/retry states.
- [ ] Build customer views for upcoming, pending, changed, completed, cancelled, and no-show appointments.
- [ ] Build admin views to create, review, approve, reject, reschedule, cancel, and record payment for appointments.
- [ ] Require customer acceptance when management proposes a changed date/time.
- [ ] Test timezone boundaries, closing time, duplicates, double submissions, rescheduling, cancellation, and payment-dependent confirmation.

### 9. Payment integration and accounting records

- [ ] Create a provider-neutral payment adapter and documented provider interface.
- [ ] Model payment attempts, allocations, references, method, status, amount, currency, gateway reference, proof, timestamps, recorder, and outstanding balance.
- [ ] Implement gateway checkout initialization for product orders and appointment bookings.
- [ ] Implement signed webhook verification, idempotency, replay protection, and event logging.
- [ ] Treat the webhook/provider verification—not the browser redirect—as payment truth.
- [ ] Support successful, pending, failed, cancelled, expired, reversed, and refunded states.
- [ ] Add bank-transfer evidence upload and admin approval if retained for Phase 1.
- [ ] Add Pay at Clinic for eligible appointment types.
- [ ] Keep booking, order, payment, and inventory transitions atomic and idempotent.
- [ ] Generate payment, order, booking, invoice, and receipt references.
- [ ] Generate printable/downloadable receipts and send email receipts.
- [ ] Add a reconciliation screen for gateway transactions and internal payments.
- [ ] Test duplicate webhooks, delayed webhooks, mismatched amounts/currency, retry, refunds, and abandoned payment.
- [ ] Complete gateway sandbox certification before live credentials are introduced.

### 10. Order management and customer dashboard

- [ ] Implement order statuses: Awaiting payment, Payment under review, Paid, Processing, Ready for pickup, Shipped, Delivered, Cancelled, Returned, and Refunded.
- [ ] Build customer overview cards, upcoming appointments, appointment history, order list/detail, tracking, receipts, saved addresses, and profile.
- [ ] Build admin order queue, order detail, fulfillment updates, cancellation, and refund initiation.
- [ ] Notify customers when important order or booking statuses change.
- [ ] Add reorder from a previous order with fresh stock/price validation.
- [ ] Ensure customer APIs enforce object-level ownership.
- [ ] Test horizontal access control so customers cannot read another customer's orders, appointments, addresses, payments, or receipts.

### 11. Phase 1 inventory operations

- [ ] Implement stock receipts, online sale deductions, POS deductions, customer returns, manual adjustments, and reservation movements.
- [ ] Store every stock movement as an append-only ledger record with reason, actor, timestamp, product/variant, quantity, and branch.
- [ ] Derive or reconcile inventory balances from controlled movements.
- [ ] Add low-stock and out-of-stock indicators.
- [ ] Add a simple admin inventory list and movement history.
- [ ] Require elevated permission and reason for manual stock changes.
- [ ] Ensure cancelled/failed orders restore reserved or deducted stock exactly once.
- [ ] Test race conditions, negative-stock prevention, refunds, cancellations, and audit history.

### 12. Online POS

- [ ] Build a keyboard- and touch-friendly POS route restricted to authorized staff.
- [ ] Add product/service search, cart, quantity, customer selection, and walk-in customer support.
- [ ] Support product-only, service-only, and combined sales.
- [ ] Support cash, Mobile Money/card gateway records, bank-transfer records, and split payments.
- [ ] Support deposits/partial payments and visible outstanding balance.
- [ ] Assign each POS session to an authorized branch and generate receipts with branch and cashier attribution.
- [ ] Prevent direct editing of completed sales.
- [ ] Implement authorized void/reversal/refund with reason and linked replacement sale.
- [ ] Add daily cashier totals and payment-method breakdown.
- [ ] Deduct stock transactionally when a sale is completed.
- [ ] Test split-payment totals, duplicate completion, reversals, refunds, insufficient stock, and unauthorized actions.

> Offline POS synchronization is a Phase 2 deliverable. Phase 1 POS requires connectivity and must clearly indicate connection loss before committing a transaction.

### 13. Admin dashboard and essential analytics

- [ ] Define each metric's formula, source, timezone, date boundary, and treatment of cancellations/refunds.
- [ ] Add cards for today's bookings, pending bookings, today's sales, product revenue, service revenue, outstanding balances, pending orders, and low stock.
- [ ] Add sales and booking trend charts.
- [ ] Add filters for date range, payment method, product category, service category, booking status, and order status.
- [ ] Add branch filter and owner-only branch-comparison views.
- [ ] Add product/service revenue, best-selling product, popular service, appointment volume, cancellation, payment-method, and stock reports.
- [ ] Add PDF, Excel, and CSV export for the reports committed to Phase 1.
- [ ] Keep product gross profit separate from estimated operating result.
- [ ] Label any incomplete-profit calculation explicitly; do not claim complete service profitability.
- [ ] Restrict financial dashboards and cost prices to authorized administrators.
- [ ] Reconcile dashboard totals against raw orders, payments, refunds, POS sales, and bookings with automated tests.

### 14. Notifications and communications

- [ ] Configure transactional email provider and authenticated sending domain.
- [ ] Create reusable branded email templates.
- [ ] Send registration verification, password reset, booking creation/change/confirmation/cancellation, payment, receipt, order, and fulfillment messages.
- [ ] Add in-system customer and admin notifications.
- [ ] Add scheduled appointment reminders at 24 hours and 6 hours.
- [ ] Add pre-filled manual WhatsApp links where required by the PRD.
- [ ] Add retry, failure logging, and delivery-status visibility for email jobs.
- [ ] Respect marketing consent; operational messages must remain separate.

### 15. Security, privacy, and operational readiness

- [ ] Create least-privilege roles for owner/admin, manager, receptionist, cashier, stock manager, service provider, and customer—even if Phase 1 activates only a subset.
- [ ] Enforce server-side permissions and object-level access on every API.
- [ ] Add CSRF/CORS/cookie settings appropriate to the final deployment topology.
- [ ] Add secure headers, HTTPS redirection, trusted proxy configuration, and secret rotation procedures.
- [ ] Add API rate limits to authentication, checkout, booking, uploads, and payment endpoints.
- [ ] Validate file type, file size, filename, and access permissions for every upload.
- [ ] Add dependency, secret, and static-code security scanning to CI.
- [ ] Add database backups and perform a restore drill.
- [ ] Add privacy, terms, cancellation/refund, and delivery/returns pages using approved legal copy.
- [ ] Add cookie/analytics consent if nonessential tracking is introduced.
- [ ] Define customer data export, correction, retention, and deletion procedures.
- [ ] Record security-sensitive and financial actions in the audit log.
- [ ] Run accessibility, responsive, cross-browser, performance, security, and payment-failure testing.

### 16. Staging, UAT, and launch

- [ ] Deploy isolated staging frontend, backend, database, worker, and object storage.
- [ ] Import approved service, product, price, stock, branch, policy, and contact data.
- [ ] Complete payment sandbox end-to-end tests and webhook verification.
- [ ] Conduct UAT for visitor, customer, admin, cashier, and fulfillment journeys.
- [ ] Verify all Ghana contact, currency, opening-hour, and policy content.
- [ ] Verify responsive UI against the supplied reference at agreed breakpoints.
- [ ] Perform database backup/restore, rollback, and incident-response drills.
- [ ] Create admin and cashier training material.
- [ ] Configure domain, TLS, production email, monitoring, alerting, and uptime checks.
- [ ] Complete a production launch checklist and obtain business sign-off.
- [ ] Run a controlled soft launch before broad promotion.
- [ ] Monitor failed payments, booking errors, overselling, stock discrepancies, email failures, and application errors daily after launch.

## Phase 1 release definition

Phase 1 is complete only when all of these journeys work with real persisted data and production-grade authorization:

- [ ] A visitor can browse responsive service and product pages.
- [ ] A customer can register, verify, sign in by email or phone, and reset a password.
- [ ] A customer can book one or more services, select an available requested time, pay or select an allowed payment option, and receive a reference and receipt.
- [ ] A customer can select an eligible branch for a service booking and only an adequately stocked branch for pickup.
- [ ] A customer can add products to a cart, reserve stock, pay, place an order, and track it.
- [ ] Administrators can manage catalogues, stock, bookings, orders, payments, and publication state.
- [ ] Cashiers can complete product/service POS sales and issue receipts.
- [ ] The owner can compare branches while branch users are restricted to their assigned branches.
- [ ] Authorized administrators can reverse/refund transactions without editing completed sales.
- [ ] Inventory stays consistent across online checkout, cancellation, refund, and POS flows.
- [ ] Dashboard totals reconcile to transaction records and can be filtered/exported.
- [ ] Email and in-system operational notifications are reliable.
- [ ] Security, privacy, accessibility, backups, monitoring, and recovery checks pass.

## Phase 2 — Advanced business operations

### 1. Staffing and permissions

- [ ] Add staff profiles, multiple roles, individual permissions, and multi-branch assignments.
- [ ] Add staff assignment to appointment service items.
- [ ] Add branch manager, receptionist, cashier, stock manager, and service-provider workspaces.
- [ ] Restrict medical, treatment, cost, profit, and audit data by role.
- [ ] Audit permission, role, and branch-assignment changes.
- [ ] Add future PRD staff modules as separately approved increments: schedules, attendance, leave, salaries, commissions, capacity, and performance analytics.

### 2. Full appointment operations

- [ ] Add telephone, WhatsApp, walk-in, child, friend, bride, and group booking workflows.
- [ ] Add check-in, in-progress, completion, no-show, staff assignment, and cross-branch moves.
- [ ] Add separate treatment records per appointment service item.
- [ ] Add treatment products, observations, reactions, allergies, medical context, notes, follow-up, and next appointment.
- [ ] Add before/after photos with separate, timestamped, withdrawable marketing consent.
- [ ] Log viewing/editing of sensitive records and restrict access to authorized management.
- [ ] Add consultation methods and enforce the separate non-refundable GHS 200 consultation fee.

### 3. Home-service and special-event workflows

- [ ] Add clinic/home eligibility per service.
- [ ] Capture Ghana/international address, map, landmark, contact, people count, event, schedule, instructions, travel, and accommodation details.
- [ ] Add branch assignment, staffing review, complete quotation, customer acceptance, payment, and management approval.
- [ ] Support bridal/group packages and international special-event requests.
- [ ] Ensure no home-service request is auto-approved before management review.

### 4. Advanced inventory and procurement readiness

- [ ] Add product batches, expiry dates, suppliers as reference data, and branch-specific balances.
- [ ] Add stock receipt, treatment consumption, transfer, damage, expiry, loss, return, count adjustment, and preorder allocation movements.
- [ ] Add standard whole-unit product recipes per service and staff consumption adjustment.
- [ ] Add physical stock-count sessions, variances, explanations, approval, and rejection.
- [ ] Add branch transfers with dispatch and receiving confirmation.
- [ ] Add reorder, expiry, out-of-stock, and preorder-available alerts.
- [ ] Defer detailed supplier/purchase-order/GRN workflows and fine-grained consumption to the later PRD increment unless separately approved.

### 5. Offline POS

- [ ] Make the POS installable as a Progressive Web App.
- [ ] Assign each device to a branch and unique device identifier.
- [ ] Cache the authorized catalogue, prices, permissions, and required customer lookup data safely.
- [ ] Queue offline transactions with temporary references and idempotency keys.
- [ ] Synchronize automatically when connectivity returns and link server references.
- [ ] Apply stock updates exactly once and flag conflicts for management.
- [ ] Add device revocation, session expiry, queue visibility, retry, and unresolved-conflict alerts.
- [ ] Conduct forced-offline, interrupted-sync, duplicate-sync, stale-price, and stock-conflict testing.

### 6. Expenses, income, and deeper analytics

- [ ] Add branch or business-wide expenses with description, amount, date, method, attachment, notes, and approval.
- [ ] Add daily/weekly/monthly sales, product/service revenue, appointment, cancellation, no-show, retention, expense, gross-profit, payment, branch, home-service, consultation, and online-order reports.
- [ ] Add new/returning customers, repeats, inactivity, abandoned carts, cancellations, no-shows, favorite services, and customer lifetime sales value.
- [ ] Add branch and staff comparisons with permission-aware drill-down.
- [ ] Clearly label estimated operating result until service costing is introduced.
- [ ] Add advanced service costing and full service-profit reporting only in its approved later increment.

### 7. Content, gallery, reviews, and approvals

- [ ] Add service packages, bridal packages, bundles, group packages, and manually renewed monthly plans.
- [ ] Add gallery categories, consent confirmation, publication state, and owner approval.
- [ ] Add verified product/service review eligibility and testimonial moderation.
- [ ] Add draft, pending approval, approved, and rejected content states.
- [ ] Require owner approval before approved service/product pricing and public content changes become visible.
- [ ] Add public About, Gallery, Bridal Packages, Testimonials, Blog, Contact, FAQ, and policy management where not completed in Phase 1.

### 8. Returns, preorders, and delivery operations

- [ ] Add full preorder payment, estimated-date changes, allocation on receipt, and customer alerts.
- [ ] Add 14-day return requests, hygiene/product-condition rules, evidence, approval, rejection reason, and refund linkage.
- [ ] Select delivery fulfillment branch based on stock and restrict pickup choices to stocked branches.
- [ ] Add worldwide manual delivery quotations, customer acceptance, payment, dispatch, and tracking notes.
- [ ] Preserve separate billing and delivery addresses.

### 9. Notifications, audit, and governance

- [ ] Add all customer and management notification events listed in the PRD.
- [ ] Add management alerts for bank evidence, quotations, returns, reviews, stock, expiry, consent withdrawal, and offline conflicts.
- [ ] Capture immutable audit events with user, role, action, record, before/after values, branch, timestamp, IP/device, and reason.
- [ ] Add an authorized audit viewer with filters and export.
- [ ] Add scheduled retention policies, backup evidence, data export/deletion handling, and periodic permission reviews.

## Phase 2 release definition

- [ ] The owner can see and compare the whole business while branch users see only assigned branches.
- [ ] Every operational and financial record has correct branch and actor attribution.
- [ ] Full clinic, consultation, home-service, walk-in, group, and treatment-record workflows operate safely.
- [ ] Branch stock, consumption, counts, transfers, expiry, and preorder movements reconcile.
- [ ] POS continues during temporary internet loss and resolves synchronization conflicts safely.
- [ ] Expenses, estimated operating result, retention, staff, and branch reporting reconcile to source records.
- [ ] Sensitive records, consent, content approval, refunds, reversals, and permissions have complete audit trails.
- [ ] All applicable PRD acceptance criteria pass in staging and production smoke tests.

## Recommended implementation order

The critical path is:

```text
Foundation and decisions
    -> Design system and application shell
    -> Authentication and customer profiles
    -> Service and product catalogues
    -> Cart, stock reservation, and appointment booking
    -> Payments and webhook reconciliation
    -> Orders, customer dashboard, and notifications
    -> POS and essential inventory
    -> Admin analytics and reports
    -> Security hardening, UAT, and Phase 1 launch
    -> Branch controls and staffing
    -> Full operations, offline POS, and Phase 2 launch
```

Parallel work is safe where contracts are agreed first: public UI can proceed alongside catalogue APIs; dashboard UI can proceed alongside metric definitions; email templates can proceed alongside booking/order state machines. Payment, stock reservation, and final order/booking transitions should be integrated only after their transactional rules and idempotency contracts are reviewed together.

## Definition of done for every backlog item

An item is not complete until:

- [ ] Acceptance behavior is documented and traced to the PRD or an approved change.
- [ ] Backend permissions and validation are enforced independently of the UI.
- [ ] Database migration and rollback implications are reviewed.
- [ ] Automated happy-path, validation, authorization, and failure tests pass.
- [ ] Loading, empty, error, and retry states are implemented.
- [ ] Responsive and keyboard-accessible behavior is verified.
- [ ] Logs contain enough context to diagnose failures without exposing secrets or sensitive data.
- [ ] API schema and relevant user/developer documentation are updated.
- [ ] Code review, CI, staging verification, and product acceptance are complete.

## Change control

The PRD remains the source of truth for business behavior. UI screenshots are visual references only and cannot override the PRD. This roadmap changes delivery sequencing, not the final product intent. Any addition, removal, or behavior change should be recorded with its PRD reference, rationale, phase, acceptance criteria, and approver before implementation.
