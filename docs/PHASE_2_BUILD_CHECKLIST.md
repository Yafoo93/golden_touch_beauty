# Phase 2 Build Checklist - Advanced Business Operations

This is the practical, plain-language build order for Phase 2. It starts after
the Phase 1 commerce, booking, management, reporting, and connected POS launch.
It explains the pages, APIs, database records, permissions, background work,
and tests required at each stage.

The [Development Roadmap](DEVELOPMENT_ROADMAP.md) and approved Product
Requirements Document remain authoritative. Where a UI reference conflicts
with the PRD, the PRD controls system behaviour.

## How we will use this checklist

- Work from Stage 0 forward unless a later task has no unmet dependency.
- Implement one checklist item or one clearly named group at a time.
- Build the backend and frontend together whenever the feature has a UI.
- Do not tick an item merely because a page exists; its real API, permissions,
  branch scope, validation, loading/error states, and audit behaviour must work.
- After each item, record what it does, why it matters, the files changed, the
  automated checks run, and the exact manual test the user should perform.
- Tick the item only after those checks pass. Keep business, legal, clinical,
  employment, and accounting decisions unticked until Golden Touch approves
  them explicitly.
- The PRD takes priority over this checklist, and this checklist takes priority
  over presentation-only behaviour inferred from screenshots.

## What Phase 2 will deliver

At the end of Phase 2:

- Staff can work within assigned roles, branches, schedules, and service duties.
- Appointments can move safely through check-in, treatment, follow-up, and
  sensitive treatment-record workflows.
- Golden Touch can quote and manage home, bridal, group, and international
  service requests without auto-approving them.
- Inventory includes batches, expiry, treatment consumption, transfers, counts,
  losses, returns, and preorder allocation.
- Authorized POS devices can continue during a temporary connection loss and
  synchronize every transaction exactly once.
- Management can record expenses and understand customer, staff, branch, and
  operational performance using reconciled reports.
- Public content, reviews, packages, prices, consent, and approvals are governed
  through complete audit trails.

## Main Phase 2 areas

| Area | Example routes | Primary users |
| --- | --- | --- |
| Staff operations | `/management/staff`, `/staff` | Owner, managers, staff |
| Advanced appointments | `/management/bookings/[reference]/treatments` | Reception, providers, managers |
| Home and event services | `/home-services`, `/management/home-services` | Customers and management |
| Advanced inventory | `/management/inventory/transfers`, `/management/stock-counts` | Stock managers |
| Offline POS | `/pos`, `/pos/sync` | Cashiers and managers |
| Finance and analytics | `/management/expenses`, `/management/reports/advanced` | Owner and authorized managers |
| Content governance | `/management/content-approvals` | Editors and owner |
| Returns and delivery | `/account/returns`, `/management/returns` | Customers and fulfillment staff |
| Governance | `/management/audit-log`, `/management/privacy-requests` | Owner and authorized administrators |

The route names below are the intended application contract. A route may be
adjusted during implementation only when the replacement is documented and all
navigation, tests, and API contracts are updated together.

---

## Stage 0 - Approve Phase 2 operating rules

No feature should be coded against guessed employment, clinical, delivery, or
financial rules. This stage records decisions needed by later stages.

### Business decisions

- [ ] Approve Phase 2 scope, budget, milestones, and release target.
- [ ] Confirm staff roles and the permission matrix for owner, branch manager,
  receptionist, cashier, stock manager, service provider, content editor, and
  finance user.
- [ ] Confirm which roles may view or change medical context, treatment notes,
  before/after photographs, cost prices, profit, salaries, commissions, audit
  history, refunds, and reversals.
- [ ] Confirm appointment capacity rules, provider assignment, working hours,
  breaks, leave, attendance, and cross-branch cover.
- [ ] Confirm consultation eligibility and the PRD's separate non-refundable
  GHS 200 consultation fee before activating it in production.
- [ ] Confirm clinic/home eligibility, travel charges, service areas, quotation
  expiry, deposits, cancellation rules, international travel, and accommodation.
- [ ] Approve treatment form templates, required clinical fields, photograph
  consent wording, retention period, and authorized viewers.
- [ ] Confirm inventory batch, expiry, recipe, stock-count, transfer, damage,
  loss, return, and approval procedures.
- [ ] Confirm expense categories, approval thresholds, attachment rules, and who
  can see business-wide versus branch finance.
- [ ] Confirm review eligibility, package rules, monthly-plan renewal behaviour,
  content approvers, and price-change approval workflow.
- [ ] Confirm preorder, return, delivery quotation, dispatch, and tracking rules.
- [ ] Complete a privacy/legal review for sensitive treatment data, photographs,
  staff data, data export, deletion, and retention.

### Technical decisions

- [ ] Approve the offline POS conflict rules for stale prices, revoked access,
  insufficient server stock, duplicate references, and expired sessions.
- [x] Select secure production object storage for treatment images, attachments,
  evidence, and exports; private files must not use public media URLs.
- [ ] Select background-job, scheduler, monitoring, backup, and error-reporting
  infrastructure suitable for Phase 2 workloads.
- [ ] Define data migration and rollback plans for every Phase 2 release.

### Result

The team has written rules for permissions, staffing, clinical records, home
services, inventory, offline sales, finance, approvals, returns, and privacy.
Later implementation does not rely on invented business behaviour.

---

## Stage 1 - Extend the Phase 2 engineering foundation

### Backend foundation

- [ ] Add feature flags for staffing, treatment records, home services,
  advanced inventory, offline POS, expenses, content approvals, and returns.
- [ ] Add reusable model fields/mixins for branch, actor, approval state,
  timestamps, archival state, and immutable references.
- [ ] Add private-file storage with signed, short-lived download URLs and
  authorization checks before every download.
- [ ] Add background queues for notifications, reminders, exports, image work,
  retention, and offline-POS reconciliation.
- [ ] Add scheduled jobs with locking so a task cannot run twice concurrently.
- [ ] Add idempotency keys to every retryable command and synchronization API.
- [ ] Add optimistic concurrency/version fields where two staff members may
  update the same operational record.
- [ ] Add an outbox or equivalent transaction-safe event mechanism so database
  changes and queued notifications cannot disagree.
- [ ] Add pagination, filters, search, ordering, and export conventions to every
  new management API.
- [ ] Add database indexes and query-count limits for new high-volume records.

### Quality and delivery

- [ ] Extend CI to run Phase 2 migrations, permission tests, API tests, frontend
  tests, offline tests, accessibility checks, and production builds.
- [ ] Add staging fixtures that contain no real customer, staff, medical, or
  financial data.
- [ ] Add monitoring for job failures, sync conflicts, expiring stock, failed
  notifications, storage failures, and unusual access to sensitive records.
- [ ] Document recovery procedures for failed jobs, partial imports, interrupted
  synchronization, and migration rollback.

### Result

Phase 2 modules share safe branch attribution, approvals, private storage,
background processing, retry behaviour, and observable failures.

---

## Stage 2 - Build staff profiles, roles, and branch permissions

Phase 1 assignments are extended rather than replaced. Existing users and
branch restrictions must continue working throughout the migration.

### Data and permission work

- [ ] Create `StaffProfile` records linked one-to-one with staff user accounts.
- [ ] Extend staff-to-branch assignments with roles, effective dates, active
  state, primary branch, individual grants, and individual denials.
- [ ] Support multiple roles and multiple branches without merging their scopes.
- [ ] Create permission definitions for bookings, treatment records, photos,
  customers, prices, costs, profit, inventory, expenses, payroll, content,
  refunds, reports, offline devices, and audit history.
- [ ] Deny access by default when neither a role nor explicit grant permits it.
- [ ] Ensure deactivation immediately blocks new sessions and offline sync.
- [ ] Record immutable audit events for invitations, activation, deactivation,
  role changes, branch changes, grants, denials, and manager changes.

### Management pages

- [ ] `/management/staff` - search and filter staff by branch, role, and status.
- [ ] `/management/staff/new` - invite or create an authorized staff account.
- [ ] `/management/staff/[id]` - edit profile, assignments, roles, permissions,
  employment state, and emergency contact where approved.
- [ ] `/management/staff-access` - permission matrix and access review dashboard.
- [ ] `/management/staff-access/reviews` - periodic permission-review records.

### Staff workspace

- [ ] `/staff` - role-aware work overview for the logged-in staff member.
- [ ] `/staff/appointments` - assigned and branch-visible appointments.
- [ ] `/staff/profile` - permitted personal and employment information.
- [ ] Show only navigation and actions the logged-in user can actually perform.

### Tests

- [ ] Test every role against every new API action.
- [ ] Test owner-wide, multi-branch, single-branch, expired, inactive, and revoked
  assignments.
- [ ] Test guessed IDs and cross-branch list, detail, update, export, and file
  download attempts.
- [ ] Test that receptionists and cashiers cannot see treatment, cost, profit,
  payroll, or audit data without an explicit approved grant.

### Result

Every staff member has an explicit identity, role, and branch scope. Permissions
are reusable, auditable, deny-by-default, and enforced in both UI and API.

---

## Stage 3 - Add schedules, attendance, leave, capacity, and commissions

This roadmap increment must be separately approved before salary or commission
figures become production payroll truth.

### Scheduling and capacity

- [ ] Create staff working schedules, recurring shifts, breaks, exceptions,
  branch cover, and service qualifications.
- [ ] Create leave requests with type, dates, reason, attachment, approval,
  rejection, cancellation, and history.
- [ ] Create attendance clock-in/out records with branch, source, corrections,
  approver, and reason.
- [ ] Derive provider capacity from schedule, qualifications, leave, breaks,
  assigned services, and existing appointments.
- [ ] Prevent assignment to unavailable, unqualified, inactive, or wrong-branch
  providers unless an authorized override records a reason.

### Pages

- [ ] `/management/staff/schedules` - branch calendar and shift management.
- [ ] `/management/staff/attendance` - daily attendance and corrections.
- [ ] `/management/staff/leave` - leave queue and calendar.
- [ ] `/management/staff/commissions` - approved commission rules and results.
- [ ] `/staff/schedule` - personal schedule and assigned branch.
- [ ] `/staff/attendance` - clock-in/out and attendance history.
- [ ] `/staff/leave` - request and track leave.

### Salary, commission, and performance safeguards

- [ ] Model effective-dated salary and commission rules without rewriting
  historical calculations.
- [ ] Calculate commissions only from eligible completed and paid transactions,
  subtracting approved refunds/reversals according to the approved rules.
- [ ] Require approval before commission results become final.
- [ ] Restrict salary and individual performance data to approved roles.
- [ ] Label all payroll output as operational support until legal/accounting
  approval confirms it is the payroll system of record.

### Result

Management can schedule staff and understand capacity while staff can see their
own shifts, attendance, leave, and approved commission information.

---

## Stage 4 - Build full appointment operations

### Booking sources and participants

- [ ] Extend booking source to website, telephone, WhatsApp, walk-in, staff,
  home service, bridal/event, and other approved sources.
- [ ] Support self, child, friend, bride, group, and walk-in recipients while
  keeping the paying customer and treatment recipient distinct.
- [ ] Support one provider per appointment service item and multiple providers
  within one booking where necessary.
- [ ] Assign or move a booking/service item only to an eligible provider and
  branch, preserving full history.

### Operational workflow

- [ ] Add explicit actions for arrival, check-in, start, pause where approved,
  complete, cancel, reject, reschedule, no-show, and follow-up required.
- [ ] Enforce valid transitions on the server; never trust a status supplied by
  the browser without checking the current record.
- [ ] Record action time, actor, branch, reason, and before/after values.
- [ ] Require authorization and reason for cross-branch moves, provider changes,
  reopened appointments, duplicate overrides, and post-completion corrections.
- [ ] Recalculate capacity and notify affected staff/customer after approved
  time, provider, branch, or service changes.

### Consultation workflow

- [ ] Create consultation service/type records and eligibility rules.
- [ ] Charge the separately approved non-refundable GHS 200 consultation fee.
- [ ] Keep consultation payment and outcome distinct from later treatment fees.
- [ ] Capture consultation method, outcome, recommendation, and follow-up.

### Pages

- [ ] Enhance `/management/bookings` with provider, source, recipient type,
  consultation, arrival, and treatment-state filters.
- [ ] Enhance `/management/bookings/[reference]` with timeline, assignments,
  check-in controls, service-item progress, and authorized corrections.
- [ ] `/staff/appointments/[reference]` - provider's permitted operational view.
- [ ] `/management/consultations` - consultation queue and status.

### Result

Phone, WhatsApp, website, walk-in, recipient, group, and consultation bookings
can be operated from request through attendance and completion with full history.

---

## Stage 5 - Build treatment records and photograph consent

Treatment records are sensitive. They must never be exposed merely because a
user can see the associated booking.

### Records

- [ ] Create one treatment record per appointment service item where required.
- [ ] Store treatment products used, quantities, observations, skin/hair/body
  reactions, allergies, relevant medical context, notes, advice, follow-up date,
  and recommended next appointment.
- [ ] Version treatment records or preserve immutable revisions after completion.
- [ ] Separate operational booking notes from restricted treatment information.
- [ ] Add structured templates by service/category with required-field rules.
- [ ] Require provider signature/confirmation and authorized correction reason.

### Photographs and consent

- [ ] Store before/after photographs privately with type, capture time, uploader,
  treatment link, branch, and integrity metadata.
- [ ] Capture treatment-documentation consent separately from public marketing
  consent.
- [ ] Record consent version, wording, time, channel, actor, withdrawal time,
  scope, and evidence.
- [ ] Stop future marketing use immediately after withdrawal without destroying
  records that must legally be retained.
- [ ] Prevent private image URLs from being indexed, guessed, or reused after
  signed-link expiry.

### Pages

- [ ] `/management/bookings/[reference]/treatments` - restricted treatment list.
- [ ] `/management/treatments/[id]` - view/edit according to record state.
- [ ] `/staff/treatments/[id]` - assigned provider treatment workspace.
- [ ] `/account/consent/photos` - customer consent status and withdrawal action.

### Security tests

- [ ] Test every role and branch against treatment records and private files.
- [ ] Log and test sensitive-record view, creation, edit, download, export, and
  consent actions.
- [ ] Ensure API errors and application logs never include medical notes or
  signed private-file URLs.

### Result

Authorized providers can document each treatment safely, while access,
photographs, corrections, and consent remain private and auditable.

---

## Stage 6 - Build home-service, bridal, group, and event quotations

### Customer experience

- [ ] `/home-services` - explain eligible services and management approval.
- [ ] `/home-services/request` - multi-step request form.
- [ ] `/bridal-packages` - live approved packages and request action.
- [ ] `/account/service-requests` - request, quote, payment, and status history.
- [ ] `/account/service-requests/[reference]` - full customer-visible detail.

### Request information

- [ ] Capture clinic/home/event type, eligible services/packages, Ghana or
  international address, country, region, city, map point/link, landmark,
  primary contact, recipient/group, people count, event type, preferred dates,
  schedule, instructions, accessibility, travel, and accommodation.
- [ ] Store separate billing and service addresses.
- [ ] Allow supporting attachments through private validated uploads.
- [ ] Clearly state that submission is a request, not an approved appointment.

### Management workflow

- [ ] `/management/home-services` - filterable review queue.
- [ ] `/management/home-services/[reference]` - staffing, travel, quotation,
  internal notes, customer messages, approval, rejection, and history.
- [ ] Assign an originating/fulfilling branch before quotation approval.
- [ ] Create itemized, versioned quotations containing services, products,
  people, travel, accommodation, discounts, taxes/fees, expiry, and total.
- [ ] Require customer acceptance of the exact quotation version.
- [ ] Require approved payment/deposit and final management approval before
  creating confirmed appointments or reserving staff.
- [ ] Expire stale quotations and preserve superseded versions.

### Result

Golden Touch can safely quote home, bridal, group, and international work. No
request is auto-approved, and accepted scope, price, payment, staff, and branch
remain traceable.

---

## Stage 7 - Build advanced inventory and treatment consumption

### Data model and movements

- [ ] Create suppliers as approved reference data without yet implementing full
  purchase orders or goods-received notes.
- [ ] Create product batches with supplier, batch number, received date, expiry,
  cost snapshot, branch, and quantities.
- [ ] Extend the append-only stock ledger for receipt, online/POS sale,
  reservation, release, treatment consumption, transfer dispatch/receive,
  damage, expiry, loss, customer return, count adjustment, and preorder allocation.
- [ ] Require branch, actor, reason, source record, batch where applicable, and
  idempotency key on every movement.
- [ ] Prevent negative on-hand, reserved, batch, and available quantities.

### Service recipes and consumption

- [ ] Create effective-dated whole-unit product recipes per service and branch
  where necessary.
- [ ] Propose expected consumption when treatment completes.
- [ ] Allow an authorized provider/stock user to adjust actual consumption with
  a reason before posting movements.
- [ ] Never silently rewrite historical consumption when a recipe changes.

### Pages

- [ ] `/management/inventory/batches` - batches, expiry, and available quantity.
- [ ] `/management/inventory/receipts/new` - receive stock into a branch/batch.
- [ ] `/management/inventory/consumption` - expected versus actual treatment use.
- [ ] `/management/inventory/recipes` - service product recipes.
- [ ] `/management/suppliers` - supplier reference records.

### Alerts

- [ ] Notify authorized staff of low stock, no stock, upcoming expiry, expired
  batches, unusual consumption, and preorder stock arrival.
- [ ] Block sale/use of expired batches and prioritize approved batch allocation
  rules such as first-expiring-first-out.

### Result

Stock explains not only sales but also receipts, batches, treatment use, damage,
expiry, loss, returns, and preorder allocation without editing ledger history.

---

## Stage 8 - Build stock counts and branch transfers

### Stock counts

- [ ] `/management/stock-counts` - sessions by branch, state, and date.
- [ ] `/management/stock-counts/new` - freeze a count scope and assign counters.
- [ ] `/management/stock-counts/[reference]` - capture counts and variances.
- [ ] Support draft, in progress, submitted, approved, rejected, and posted states.
- [ ] Require explanations for configured variances and approval before ledger
  adjustments are posted.
- [ ] Prevent editing after posting; corrections use a linked adjustment.

### Transfers

- [ ] `/management/inventory/transfers` - branch transfer queue.
- [ ] `/management/inventory/transfers/new` - request products/batches/quantities.
- [ ] `/management/inventory/transfers/[reference]` - approve, dispatch, receive,
  reject, cancel, and inspect history.
- [ ] Support requested, approved, rejected, dispatched, partially received,
  received, cancelled, and discrepancy states.
- [ ] Move stock out of source availability at dispatch and into destination
  stock only upon receiving confirmation.
- [ ] Record shortage, excess, damage, and batch discrepancy without silently
  changing the dispatched record.

### Tests

- [ ] Test simultaneous sales, counts, transfers, reservations, and treatment use.
- [ ] Reconcile every posted count/transfer with the append-only stock ledger.
- [ ] Test cross-branch permissions and approval separation.

### Result

Physical counts and branch transfers reconcile through explicit approvals and
ledger movements, including discrepancies and partial receiving.

---

## Stage 9 - Build offline-capable POS

Offline support is limited to temporary network loss. It must not weaken staff,
branch, price, stock, payment, or audit controls.

### Installable application and device control

- [ ] Add a valid PWA manifest, icons, service worker, install experience, and
  offline shell for authorized POS routes.
- [ ] Create POS device records with unique ID, branch, label, status, last sync,
  app version, registered-by, and revoked-at fields.
- [ ] `/management/pos/devices` - register, monitor, and revoke devices.
- [ ] Bind each offline session to an authorized staff member and device branch.
- [ ] Expire cached authorization and require online revalidation at the approved
  interval; revocation blocks the next sync/use as designed.

### Safe local data

- [ ] Cache only the minimum authorized catalogue, variants, prices, services,
  tax/payment configuration, permissions, and customer lookup data.
- [ ] Encrypt or otherwise protect sensitive local data using the approved
  browser/device threat model.
- [ ] Never cache passwords, session secrets, treatment records, full medical
  context, raw card details, or unnecessary customer data.
- [ ] Display catalogue age, last successful sync, offline state, and actions
  unavailable offline.

### Offline transaction queue

- [ ] Create client-generated temporary references and idempotency keys.
- [ ] Store immutable queued sale snapshots with device, cashier, branch,
  customer/walk-in, lines, prices, costs where permitted, payments, and times.
- [ ] Permit only approved offline payment methods; never claim an unverified
  gateway payment succeeded while offline.
- [ ] Prevent local duplicate completion and editing of completed queued sales.
- [ ] Synchronize automatically in deterministic order when connectivity returns.
- [ ] Apply each server sale and stock deduction exactly once.

### Conflict workflow

- [ ] Detect duplicate sync, stale price, missing item, inactive service, revoked
  staff/device, wrong branch, insufficient stock, and reference conflicts.
- [ ] `/pos/sync` - cashier queue and sync status.
- [ ] `/management/pos/sync-conflicts` - authorized resolution queue.
- [ ] Preserve original queued data and every attempted/resolved outcome.
- [ ] Require authorization and reason for conflict acceptance, replacement,
  refund, reversal, or stock correction.

### Tests

- [ ] Test forced offline mode, browser restart, interrupted sync, repeated sync,
  multiple devices, stale price, insufficient stock, revoked access, expired
  sessions, and server timeout after receiving a transaction.
- [ ] Prove that retrying the same transaction cannot duplicate sale, payment,
  receipt, stock movement, income, commission, notification, or audit records.

### Result

An authorized cashier can complete approved sales during temporary internet
loss and synchronize safely, with conflicts visible instead of silently lost.

---

## Stage 10 - Build expenses, income, and financial controls

### Expense records and approvals

- [ ] Create expense categories and effective status.
- [ ] Create branch or business-wide expenses with reference, description,
  amount, date, payment method, payee, attachment, notes, recorder, branch,
  approval state, approver, and history.
- [ ] Support draft, submitted, approved, rejected, paid, cancelled, and reversed
  states according to approved accounting rules.
- [ ] Require approval based on role and configured amount thresholds.
- [ ] Preserve corrections through reversal/replacement rather than editing
  approved financial history.

### Pages

- [ ] `/management/expenses` - permitted expense list and totals.
- [ ] `/management/expenses/new` - record and submit an expense.
- [ ] `/management/expenses/[reference]` - evidence, approval, payment, history.
- [ ] `/management/expense-categories` - approved categories.
- [ ] `/management/income` - reconciled income sources, not manually invented sales.

### Financial reporting

- [ ] Add income, expense, estimated operating result, and cash-flow-support
  reports by date, branch, category, method, status, and source.
- [ ] Reconcile income to successful online payments, completed POS entries,
  approved manual records, refunds, and reversals.
- [ ] Exclude pending/rejected expenses from approved totals.
- [ ] Clearly label estimated operating result until complete service costing,
  payroll, tax, depreciation, and other accounting treatment are approved.
- [ ] Provide branded PDF, Excel, and CSV exports with formula/provenance notes.

### Result

Authorized management can record and approve expenses and compare them with
reconciled income without presenting an estimate as statutory profit.

---

## Stage 11 - Build deeper customer, staff, service, and branch analytics

### Customer analytics

- [ ] Report new versus returning customers using a documented identity rule.
- [ ] Report repeat bookings/orders, inactivity, abandoned carts, cancellations,
  no-shows, favorite services/products, retention, and lifetime sales value.
- [ ] Define cohorts, observation windows, timezone, refunds, guest/walk-in
  handling, merged identities, and zero-denominator behaviour.

### Operational analytics

- [ ] Add consultation, home-service, quotation acceptance, treatment completion,
  inventory consumption, expiry/loss, transfer, return, preorder, and delivery
  reports.
- [ ] Add staff comparisons only for authorized users and define attribution for
  shared bookings, multiple providers, refunds, reassignment, and commissions.
- [ ] Add branch comparisons with permission-aware drill-down.
- [ ] Extend daily, weekly, and monthly trends with consistent local date bounds.

### Accuracy

- [ ] Add a written formula, source, inclusion, exclusion, and limitation for
  every new dashboard and report number.
- [ ] Add automated reconciliation tests against raw transaction records.
- [ ] Test refunds, reversals, rejected expenses, cancelled appointments, no-show,
  partial payments, date boundaries, cross-branch work, and offline sync.
- [ ] Prevent small-group reports from exposing sensitive customer or staff data.

### Result

Management can understand retention, staff, home-service, consultation,
inventory, expense, and branch performance using documented, tested figures.

---

## Stage 12 - Build packages, reviews, gallery, and content approvals

### Packages and plans

- [ ] Create service packages, bridal packages, bundles, group packages, and
  manually renewed monthly plans with branch/service eligibility.
- [ ] Store package items, quantities, price snapshots, validity, usage limits,
  publication dates, terms, and remaining entitlement.
- [ ] Do not silently auto-renew monthly plans or charge a customer without a
  separately approved recurring-payment implementation.
- [ ] Add package purchase, booking, redemption, expiry, cancellation, and refund
  history.

### Reviews and gallery

- [ ] Allow reviews only after verified eligible product purchase or completed
  service, retaining the linked eligibility record internally.
- [ ] Add rating, review text, media where approved, moderation, response,
  publication, report, and removal workflows.
- [ ] Add gallery categories, service/branch tags, consent confirmation, owner
  approval, display order, and publication schedule.
- [ ] Automatically prevent/withdraw publication when required consent is absent
  or withdrawn.

### Approval workflow

- [ ] Support draft, pending approval, approved, rejected, scheduled, published,
  withdrawn, and archived states where applicable.
- [ ] `/management/content-approvals` - owner approval queue.
- [ ] `/management/content-approvals/[id]` - compare proposed/current values,
  evidence, decision, reason, and history.
- [ ] Require owner approval before approved service/product prices, packages,
  gallery items, testimonials, reviews, blog articles, and key public content
  become visible.
- [ ] Prevent an author from approving their own change when separation of duties
  is required.

### Public and management pages

- [ ] Upgrade `/bridal-packages`, `/gallery`, `/testimonials`, `/blog`, `/about`,
  `/contact`, `/faq`, and policy pages to database-backed approved content.
- [ ] Add management CRUD and preview for packages, reviews, blog, FAQs, and
  policy versions where Phase 1 management does not already cover them.

### Result

Only eligible reviews and owner-approved prices, packages, images, testimonials,
articles, and operational content appear publicly.

---

## Stage 13 - Build preorders, returns, delivery quotations, and tracking

### Preorders

- [ ] Allow preorder only on explicitly enabled variants with an estimated date.
- [ ] Require full payment unless an approved rule says otherwise.
- [ ] Keep preorder funds, ordered quantity, branch, allocation, estimated-date
  history, customer acceptance/cancellation, and refund linkage traceable.
- [ ] Allocate received stock transactionally and notify customers in order of
  the approved allocation policy.

### Customer returns

- [ ] `/account/returns` - customer's return requests and status.
- [ ] `/account/returns/new` - select eligible order lines, quantity, reason, and
  validated evidence.
- [ ] `/account/returns/[reference]` - decision, instructions, refund, and history.
- [ ] Enforce the approved 14-day window, hygiene exclusions, condition rules,
  quantity limits, prior returns, and order ownership on the server.

### Management returns

- [ ] `/management/returns` - branch/status/date/reason queue.
- [ ] `/management/returns/[reference]` - inspect evidence, approve/reject with
  reason, receive goods, assess condition, restock/write off, and link refund.
- [ ] Ensure returned stock enters inventory only after authorized inspection.
- [ ] Prevent refund and stock restoration from occurring more than once.

### Delivery quotation and tracking

- [ ] Select the fulfillment branch based on stock and permission-safe rules;
  pickup choices remain limited to branches with available stock.
- [ ] Support worldwide manual delivery quotations with price, currency, carrier,
  expiry, notes, and customer acceptance.
- [ ] Require accepted delivery price and payment before dispatch where required.
- [ ] Store packing, dispatch, carrier, tracking reference/link, status events,
  attempted delivery, delivery evidence, and authorized correction history.
- [ ] Preserve distinct billing, delivery, pickup, and home-service addresses.

### Result

Preorders, customer returns, stock restoration, refunds, worldwide quotations,
dispatch, and tracking are controlled by explicit eligibility and audit rules.

---

## Stage 14 - Complete notifications, audit, privacy, and governance

### Notification coverage

- [ ] Create a notification-event matrix for customers, providers, reception,
  stock users, cashiers, managers, finance users, and owner.
- [ ] Add events for staff assignment, schedule/leave, consultation, check-in,
  treatment follow-up, consent withdrawal, home-service review, quotation,
  return, preorder, delivery, stock/expiry, expense approval, content approval,
  offline conflict, and permission review.
- [ ] Respect operational-versus-marketing preferences and channel consent.
- [ ] Ensure retrying delivery never repeats the underlying business action.
- [ ] Add template versioning, delivery attempts, failure state, and support-safe
  diagnostics without leaking sensitive content.

### Audit controls

- [ ] Capture immutable user, role, action, record type/reference, branch,
  before/after values, time, reason, request ID, IP, and appropriate device data.
- [ ] Redact passwords, secrets, tokens, raw payment data, and unnecessary medical
  content from audit payloads.
- [ ] Enhance `/management/audit-log` with authorized filters and exports.
- [ ] Alert on unusual sensitive-record access, repeated denial, permission
  escalation, bulk export, device conflict, and destructive corrections.

### Privacy and lifecycle

- [ ] `/management/privacy-requests` - access/export/correction/deletion queue.
- [ ] Implement verified customer data export in a safe, portable format.
- [ ] Implement deletion/anonymization rules that preserve legally required
  financial, audit, consent, and treatment records.
- [ ] Add scheduled retention actions with dry-run, approval, result evidence,
  and failure alerts.
- [ ] Add periodic permission reviews and proof of completion.
- [ ] Capture backup evidence and test restoration of database and private files.

### Result

Important Phase 2 activity generates the right notifications and a complete,
privacy-aware audit trail, with controlled retention and data-rights handling.

---

## Stage 15 - Security, migration, UAT, training, and Phase 2 launch

### Migration and compatibility

- [ ] Back up production before applying Phase 2 migrations.
- [ ] Test migrations against a recent anonymized production-sized database.
- [ ] Verify existing Phase 1 users, assignments, bookings, orders, payments,
  stock, POS sales, reports, receipts, and links remain correct.
- [ ] Test rollback or forward-fix procedures and feature-flag shutdown.

### Security and quality checks

- [ ] Test every API permission, object ownership, and branch restriction.
- [ ] Test treatment records, private files, consent, staff/payroll data, expense
  evidence, exports, offline cache, and sync endpoints for unauthorized access.
- [ ] Test uploads for type, size, malware-handling policy, metadata, and private
  storage access.
- [ ] Test rate limits, CSRF, CORS, sessions, device revocation, idempotency,
  concurrent operations, and replay resistance.
- [ ] Run dependency, secret, static-analysis, and production-configuration scans.
- [ ] Test keyboard, screen reader, contrast, mobile, tablet, laptop, desktop,
  Chrome, Edge, Firefox, and Safari where available.
- [ ] Test slow/lost networks, duplicate clicks, refresh, worker failure, storage
  failure, email failure, and interrupted background jobs.
- [ ] Complete forced-offline POS and conflict testing on real target devices.
- [ ] Reconcile inventory, income, expenses, reports, commissions, returns, and
  offline sales with source records.

### User acceptance and launch

- [ ] Deploy all Phase 2 features disabled to staging first.
- [ ] Load approved roles, staff, schedules, recipes, suppliers, categories,
  templates, packages, expense rules, and notification templates.
- [ ] Complete workflow UAT with owner, managers, receptionists, providers,
  cashiers, stock managers, content editors, and finance users.
- [ ] Train each role using only its permitted workspace and document support
  procedures.
- [ ] Run a pilot at one branch/device before enabling both branches.
- [ ] Monitor errors, queues, conflicts, stock reconciliation, sensitive access,
  notification failures, and performance during controlled rollout.
- [ ] Obtain documented business, privacy, security, and operational sign-off.
- [ ] Enable Phase 2 features gradually with a tested rollback plan.

### Result

Phase 2 launches without breaking Phase 1, and staff can operate the expanded
platform safely across Makola and Tse Addo.

---

## Phase 2 release definition

- [ ] The owner can compare the whole business; every other user sees only
  explicitly assigned roles, branches, records, fields, and actions.
- [ ] Every operational and financial record has correct branch and actor
  attribution.
- [ ] Clinic, consultation, home-service, walk-in, recipient, group, assignment,
  treatment, and follow-up workflows operate safely.
- [ ] Sensitive records and photographs are private, consent-aware, access-logged,
  and protected from guessed URLs.
- [ ] Batches, consumption, counts, transfers, expiry, returns, and preorder stock
  reconcile to the append-only inventory ledger.
- [ ] POS survives approved temporary offline operation and resolves every queued
  transaction exactly once or creates a visible conflict.
- [ ] Expenses, income, estimated operating result, retention, staff, service,
  customer, and branch reports reconcile to source records.
- [ ] Packages, reviews, prices, gallery, testimonials, and content follow the
  approved publication workflow.
- [ ] Returns, refunds, delivery quotations, dispatch, and tracking retain complete
  customer and management history.
- [ ] Notifications, audit, backups, restoration, retention, privacy requests,
  permission reviews, and production monitoring pass acceptance tests.
- [ ] All applicable PRD acceptance criteria pass in staging and production smoke
  tests.

## Simple Phase 2 production sequence

Use this order during implementation:

1. Approve staffing, clinical, home-service, inventory, offline, finance, and
   privacy rules.
2. Extend shared engineering, private storage, background jobs, and auditing.
3. Build staff profiles, roles, branches, and permission reviews.
4. Build schedules, attendance, leave, capacity, and approved commissions.
5. Complete appointment sources, assignments, check-in, and consultations.
6. Build protected treatment records, photographs, and consent withdrawal.
7. Build home-service, bridal, group, international request, and quotation flows.
8. Build batches, recipes, consumption, expiry, and inventory alerts.
9. Build stock counts and branch transfers.
10. Build and conflict-test offline POS.
11. Build expenses, income, and financial controls.
12. Build deeper customer, staff, service, and branch analytics.
13. Build packages, verified reviews, gallery, and content approvals.
14. Build preorders, returns, delivery quotations, dispatch, and tracking.
15. Complete notification coverage, audit, privacy, retention, and backups.
16. Migrate, test, train, pilot, monitor, and progressively launch Phase 2.

## Definition of done for every checklist item

An item is complete only when:

- [ ] Its behaviour and acceptance criteria are documented.
- [ ] Database migrations and rollback/forward-fix implications are reviewed.
- [ ] API permissions, object ownership, and branch scope are enforced server-side.
- [ ] The actual UI uses the real API where a UI counterpart exists.
- [ ] Loading, empty, validation, failure, retry, and success states work.
- [ ] Changes produce the required audit and notification events exactly once.
- [ ] Automated tests cover success, denial, invalid state, retry, concurrency,
  and cross-branch/customer access as applicable.
- [ ] Keyboard, responsive, and accessibility behaviour is checked.
- [ ] Operational documentation, formulas, support, and recovery steps are updated.
- [ ] The relevant section above is manually verified and then ticked.
