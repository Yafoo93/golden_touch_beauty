# Golden Touch Beauty Centre

<p align="center">
  <img src="docs/logo.png" alt="Golden Touch Beauty Centre logo" width="220">
</p>

<p align="center">
  <strong>Where Beauty Meets Excellence</strong><br>
  A planned multi-branch platform for beauty services, bookings, e-commerce, point of sale, inventory, customer care, and business analytics.
</p>

> [!IMPORTANT]
> This repository is currently in the **foundation stage**. It contains the Product Requirements Document (PRD), brand assets, and an initial Django backend scaffold. Most business features described below are not yet implemented and represent the approved target scope unless marked as a later-phase item.

## Table of contents

- [Overview](#overview)
- [Project status](#project-status)
- [Business context](#business-context)
- [Product goals](#product-goals)
- [Phase 1 scope](#phase-1-scope)
- [Users and access](#users-and-access)
- [Core workflows and rules](#core-workflows-and-rules)
- [Reporting and administration](#reporting-and-administration)
- [Security, privacy, and auditability](#security-privacy-and-auditability)
- [Proposed technical architecture](#proposed-technical-architecture)
- [Core domain model](#core-domain-model)
- [Roadmap](#roadmap)
- [Phase 1 acceptance criteria](#phase-1-acceptance-criteria)
- [Delivery dependencies and risks](#delivery-dependencies-and-risks)
- [Repository structure](#repository-structure)
- [Getting started](#getting-started)
- [Documentation](#documentation)

## Overview

Golden Touch Beauty Centre needs a single, responsive business-management platform that connects its customer-facing website with day-to-day branch operations. The platform will allow customers to discover services, book appointments, request home services, shop for products, make payments, and track their activity. Staff and management will use the same central system to handle bookings, sales, stock, treatment records, expenses, approvals, and reporting.

The initial rollout covers the **Makola** and **Tse Addo** branches in Accra, Ghana. Multi-branch support is a foundational requirement: every operational record must carry a branch identifier, while the owner retains a consolidated view across the business.

The primary language is English and the primary currency is Ghana cedis (GHS).

## Project status

| Area | Status |
| --- | --- |
| Product requirements | Drafted (PRD v1.0, 20 July 2026) |
| Brand asset | Available |
| UX/UI design | Not started |
| Application architecture | Initial Django/PostgreSQL backend foundation established |
| Backend | Django project scaffold, modular apps, custom user model, API docs, and health endpoint |
| Web frontend and POS | Not started |
| Payment provider | To be selected during implementation |
| Deployment environment | Not configured |

The PRD describes a proposed four-week Phase 1 delivery plan, but also notes that the schedule depends on strict scope control, prompt content delivery, payment-provider onboarding, and parallel work by an experienced team.

## Business context

### Initial branches

| Branch | Address | Operating hours |
| --- | --- | --- |
| Makola | Makola Shopping Mall, Shop 143, Second Floor, Accra, Ghana | Monday–Saturday, 7:30 a.m.–5:00 p.m. |
| Tse Addo | Tse Addo, opposite The Royal Stool Event, Accra, Ghana | Monday–Saturday, 7:30 a.m.–7:00 p.m. |

The data model must support additional branches without redesign. Services can be enabled per branch, stock is held separately per branch, and Phase 1 uses consistent product selling prices across branches.

### Brand and experience

- Primary palette: gold, white, and black.
- Style: luxurious, modern, glamorous, and consistent.
- Customer interfaces: responsive, mobile-friendly, accessible, and understandable to users with limited technical experience.
- Management interfaces: optimized for clarity, speed, and operational efficiency.
- Supported form factors: desktop, tablet, and mobile browsers, with an offline-capable desktop POS.

## Product goals

- Replace manual appointment, sales, and inventory processes with one source of truth.
- Let customers browse, book, shop, pay, track orders, and manage their history online.
- Prevent duplicate active bookings for the same customer and service.
- Track sales, appointments, stock movements, expenses, and staff actions by branch.
- Reduce stock losses and capture products consumed during treatments.
- Support clinic services, consultations, home services, bridal groups, and international special-event requests.
- Improve customer retention through treatment history, purchase history, reminders, and analytics.
- Provide reliable daily, weekly, monthly, and branch-comparison reporting.
- Preserve a complete audit trail and restrict sensitive treatment information.
- Scale to new branches, staff, services, products, and integrations.

## Phase 1 scope

### Public website

The public site will include Home, About, Services, Service Details, Appointment Booking, Home-Service Requests, Consultation, Shop, Product Details, Cart, Checkout, Gallery, Bridal Packages, Testimonials, Beauty Tips/Blog, Contact, FAQs, policies, Login, and Registration.

Visitors can browse without an account but must register or log in before booking, purchasing, saving favorites, or reviewing. The contact page will show both branches together, and enquiry actions will open WhatsApp with a pre-filled message.

### Customer account

Customers can authenticate with either email/password or phone/password. Their dashboard is expected to provide:

- Upcoming, pending, changed, and historical appointments.
- Relevant treatment history and consent controls.
- Product orders, tracking, receipts, and outstanding balances.
- Wishlist, saved addresses, purchase history, and reordering.
- Marketing and before/after photograph consent settings.

### Services, bookings, and consultations

- A service catalogue with categories, descriptions, imagery, duration, branch availability, eligibility, approval state, and flexible pricing.
- Fixed prices, starting prices, ranges, selectable price options, and management quotations.
- Multi-service bookings under one reference while retaining separate service duration, pricing, assignment, and treatment data.
- Clinic appointments, consultations, home-service requests, group bookings, and bookings made for another recipient.
- Management approval, rejection, rescheduling, branch transfer, staff assignment, check-in, in-progress, completion, cancellation, and no-show handling.
- Packages such as bridal packages, facial bundles, hair-and-makeup combinations, group packages, and manually renewed monthly beauty plans.

### Online shop

- Product catalogue, categories, search, filters, variants, wishlist, cart, checkout, and verified reviews.
- Delivery and billing addresses, clinic pickup, paid delivery orders, order tracking, and reordering.
- Manual delivery quotations for local or worldwide delivery.
- Full-payment preorders with an estimated availability date and customer notifications.
- Management-approved returns requested within 14 days, subject to product-condition and hygiene rules.
- No cash on delivery in Phase 1.

### Payments, receipts, and POS

- Mobile Money, bank transfer, cash at clinic, online payments, deposits, partial payments, and POS split payments.
- Bank-transfer proof upload and management review.
- Payment allocations that link amounts to bookings, orders, or sales and preserve outstanding balances.
- Printable, downloadable, emailable, and WhatsApp-shareable receipts.
- Product, service, and combined POS sales, including walk-in customers.
- Permission-controlled discounts, refunds, price changes, complimentary services, cancellations, and reversals.
- Offline desktop POS with a local transaction queue, automatic synchronization, temporary-to-official reference linking, and conflict alerts.

### Inventory

- Stock balances, reorder levels, batches, and expiry dates per branch.
- Stock receipts, sales, treatment consumption, transfers, damage, expiry, loss, returns, adjustments, counts, and preorder allocation.
- Whole-unit treatment consumption and optional service recipes in Phase 1.
- Physical count sessions with variance review and approval.
- Low-stock, out-of-stock, expiry, and preorder-availability alerts.
- Branch-aware product reservations during online checkout.

### Management operations

- Multi-branch administration and configurable role-based permissions.
- Customer profiles and access-controlled treatment records.
- Home-service and delivery quotation management.
- Expense entry for a branch or the whole business.
- Product, service, gallery, package, pricing, opening-hour, and contact-content management with owner approval before publication.
- Management dashboards, exports, notifications, and audit logs.

## Users and access

| User type | Intended access |
| --- | --- |
| Public visitor | Browse public content; authentication required for transactions and reviews. |
| Registered customer | Manage profile, bookings, payments, orders, receipts, wishlist, consent, and eligible reviews. |
| Owner / Super Administrator | Full cross-branch access, approvals, permissions, sensitive records, financials, reports, and audit logs. |
| Branch manager | Operate assigned branches, appointments, treatment records, stock, expenses, transfers, quotations, and content. |
| Receptionist | Register walk-ins, manage bookings and check-ins, record permitted payments, and print receipts; no sensitive medical or profit access. |
| Sales attendant / Cashier | Process sales and payments, print receipts, and view permitted sales data. |
| Stock manager | Manage inventory, receipts, transfers, losses, expiry, counts, and treatment consumption. |
| Service provider | View assigned appointments, update service status and permitted notes, and record products used. |

Roles are configurable. A staff member may hold multiple roles and belong to one or more branches. Individual permissions can be granted or revoked, with sensitive access and permission changes recorded in the audit log.

## Core workflows and rules

### Clinic booking

1. The customer selects one or more services, a branch, and a preferred date and time.
2. The customer supplies relevant treatment and recipient information and chooses a payment method.
3. The platform creates a booking reference and notifies the customer and management.
4. Management approves, rejects, moves, or proposes a new time or branch.
5. If management proposes a change, the customer must accept it before confirmation.
6. Staff check in the customer, deliver each service, record treatment details and products used, and complete the appointment.

Times are requested in 30-minute intervals within branch opening hours. A booking that may finish after closing produces a management warning rather than being rejected automatically. Authorized managers can block periods for holidays, meetings, events, maintenance, or capacity constraints.

Duplicate active bookings for the same customer and service are blocked while the earlier booking is Pending, Confirmed, Checked in, In progress, or Rescheduled awaiting acceptance. An authorized override requires a reason and audit entry.

### Booking and payment states

Public booking statuses are **Pending**, **Confirmed**, **Checked in**, **In progress**, **Completed**, **Cancelled**, **Rescheduled**, and **No-show**. Internal indicators can additionally represent payment review, proposed time changes, quotation review, or transfer verification.

- Verified full online payment: confirmed, subject to any accepted time change.
- Deposit: confirmed with the outstanding balance retained.
- Pay at Clinic: pending until management confirms or proposes a time.
- Consultation: confirmed only after the separate, non-refundable **GHS 200** fee is paid.

### Home service

The customer selects eligible services and submits the destination, map location, contact, group size, event, preferred schedule, and travel details. Management assigns a branch, assesses staffing and travel, sends a complete quotation, and approves only after customer acceptance and full payment. Phase 1 clinic-only treatments must not be offered as home services. International home service is intended for bridal or special events.

### Checkout and stock reservation

Available stock is reserved for **30 minutes** while checkout is in progress. Successful payment converts the reservation into a deduction; failed, expired, or abandoned checkout releases it. Delivery orders are fulfilled from a branch with sufficient available stock, while clinic pickup only offers adequately stocked branches.

### Completed-sale corrections

Completed sales are immutable. A correction requires an authorized cancellation or reversal, a reason, a linked replacement sale where relevant, and a complete audit trail.

### Offline POS synchronization

Each desktop POS is permanently associated with a branch, device identifier, and authorized user session. Offline transactions keep temporary references and sync automatically when connectivity returns. The server assigns official references, updates stock, links both references, and flags conflicts for management review.

## Reporting and administration

The management dashboard will surface appointments, booking changes, home-service requests, sales, product and service revenue, balances, online orders, delivery quotations, low/expiring stock, expenses, pending reviews, trends, branch comparisons, and payment-method analysis.

Reports cover sales, revenue, appointments, cancellations, no-shows, popular services, best-selling products, staff sales, retention, inventory, expiry, expenses, product gross profit, payments, branch comparison, home services, online orders, and consultations. Exports are required in **PDF, Excel, and CSV**.

Customer-retention metrics include new and returning customers, repeat bookings and purchases, inactivity, abandoned carts, cancellations, repeated no-shows, favorite services, and customer lifetime sales value.

Phase 1 financial reporting uses:

```text
Product gross profit = Product sales revenue - Cost of goods sold

Estimated operating result = Total recorded revenue
                           - Product cost of goods sold
                           - Recorded expenses
```

The second value must be labeled as an estimate because complete service-delivery costing is deferred.

## Security, privacy, and auditability

The planned baseline includes:

- Secure password hashing, HTTPS, input validation, and protection against common web attacks.
- Role- and branch-based access control, session timeout, login-attempt protection, email verification, and password reset.
- Restricted medical and treatment data, separated from routine contact data through permissions and access logging.
- Secure object/file storage for payment evidence, receipts, reports, and treatment photographs.
- Explicit, optional, timestamped, and withdrawable photograph consent, separate from marketing consent and necessary treatment storage.
- Secure payment webhooks and offline synchronization.
- Daily backups and legally required data-export/deletion procedures.
- Immutable audit records for authentication, permission, pricing, booking, stock, sales, refund, treatment-record, consent, expense, content-approval, transfer, and synchronization events.

Audit entries should capture the user, role, action, affected record, before/after values, branch, timestamp, IP address or device identifier, and a reason where required.

## Proposed technical architecture

The following stack is recommended by the PRD and remains subject to confirmation during implementation:

| Layer | Proposed technology | Responsibility |
| --- | --- | --- |
| Backend | Python, Django, Django REST Framework | Authentication, administration, workflows, API, and business rules |
| Database | PostgreSQL | Transactional relational storage and reporting |
| Frontend | Next.js or React | Responsive public, customer, and management interfaces |
| Offline POS | Progressive Web App, Service Worker, IndexedDB | Cached catalogue, local sales, and synchronization queue |
| Background jobs | Redis and Celery, or equivalent | Email, reminders, reservation expiry, reports, and synchronization |
| File storage | S3-compatible object storage | Images, proofs, receipts, treatment photographs, and report files |
| Deployment | Containerized cloud environment | Environment separation, scaling, monitoring, and backups |
| Payments | Provider adapter layer | Ghana Mobile Money, cards, refunds, and future provider changes |

The payment provider should be evaluated for Ghana Mobile Money and international card support, settlement time, fees, refunds, webhook reliability, documentation, and support.

## Core domain model

The principal entities identified by the PRD are grouped below.

- **Identity and access:** User, Customer, Customer Address, Customer Consent, Staff Member, Role, Permission, Branch, Device.
- **Services and appointments:** Service Category, Service, Service Price Option, Service Package, Appointment, Appointment Service Item, Appointment History, Home-Service Request, Consultation, Treatment Record, Treatment Photograph.
- **Catalogue and inventory:** Product Category, Product, Product Variant, Product Image, Product Batch, Branch Inventory, Stock Reservation, Stock Movement, Stock Count, Stock Count Item, Product Recipe.
- **Commerce:** Shopping Cart, Cart Item, Wishlist, Order, Order Item, Delivery Quotation, Payment, Payment Allocation, Invoice, Receipt, POS Sale, POS Sale Item.
- **Operations:** Expense, Review, Notification, Audit Log, Content Approval, Offline Transaction Queue.

All relevant operational entities must retain branch attribution. Transactional records should preserve historical values rather than relying only on mutable catalogue data.

## Roadmap

### Phase 1 — Minimum viable product

Responsive public website, accounts, clinic and home-service booking, paid consultations, e-commerce, payments, receipts, POS, offline operation, branch inventory, customer/treatment records, expenses, essential reporting, content approval, permissions, notifications, and audit logging.

### Phase 2

- Staff schedules, attendance, leave, and salaries.
- Advanced appointment capacity and automated staff assignment.
- Advanced service costing and complete service-profit analysis.
- Full WhatsApp Business API integration.
- Supplier management, purchase orders, goods received, and supplier payments.
- Barcode generation/scanning and detailed product-consumption measurements.

### Phase 3

- Mobile applications, loyalty points, referrals, and gift cards.
- Automated subscriptions and recurring beauty-plan billing.
- Discount codes, courier integration, dynamic international shipping, and multi-currency display.
- Waiting lists and customer reference-image uploads.
- Advanced forecasting, demand prediction, staff-performance scoring, and central warehouse management.

### Explicitly out of Phase 1

Native mobile apps, automated WhatsApp API messaging, barcodes, supplier/purchase-order workflows, automatic courier pricing, cash on delivery, store credit, loyalty/referrals/gift cards, recurring billing, payroll, attendance, leave, commissions, detailed service costing, waiting lists, public staff reviews, VAT calculation, wholesale accounts, and reseller accounts.

## Phase 1 acceptance criteria

The release will be considered functionally complete when it satisfies the PRD's 40 acceptance criteria, summarized as follows:

- [ ] Public visitors can browse services and products; authentication gates booking and purchasing.
- [ ] Customers can register and log in with email or phone credentials.
- [ ] A booking can contain multiple services and target Makola or Tse Addo.
- [ ] Customers can request preferred times and choose Pay at Clinic.
- [ ] Consultations require a separate, non-refundable GHS 200 payment.
- [ ] Management can approve bookings or propose changes that customers must accept.
- [ ] Duplicate active customer/service bookings are blocked, with audited management overrides.
- [ ] Eligible home services support full management quotations.
- [ ] Customers can purchase products online, including fully paid preorders.
- [ ] Checkout reserves stock for 30 minutes and deducts it after successful payment.
- [ ] Pickup selection reflects branch availability; delivery quotations are managed manually.
- [ ] POS supports products, services, split payments, temporary offline operation, and later synchronization.
- [ ] Every sale records its branch and cashier.
- [ ] Inventory is branch-specific and captures treatment consumption, counts, low stock, and expiry.
- [ ] Completed sales cannot be edited; corrections use authorized, audited reversals.
- [ ] Customers receive automatic email receipts; management receives email and in-system notifications.
- [ ] Sensitive treatment information is visible only to authorized management.
- [ ] Product and service publication changes require owner approval.
- [ ] Reports export to PDF, Excel, and CSV and support branch comparison.
- [ ] The platform maintains a complete audit log and works on desktop and mobile browsers.

Refer to the PRD for the normative, individually numbered acceptance criteria.

## Delivery dependencies and risks

### Business inputs required

- Final service catalogue, descriptions, duration, pricing, and photographs.
- Product catalogue, variants, cost/selling prices, opening stock, batches, expiry data, and images.
- Staff list and branch contact/location details.
- Bank and Mobile Money details and the selected payment provider.
- Legal and operational policies, social links, gallery content, and email accounts.
- Hosting, domain, and environment decisions.

### Principal risks

| Risk | Likely impact | Planned response |
| --- | --- | --- |
| Payment-provider approval delays | Online payments may miss launch | Start onboarding early; retain bank transfer and Pay at Clinic options |
| Offline stock conflicts | Offline sales may conflict with online inventory | Use branch stock, queued transactions, conflict alerts, and controlled permissions |
| Incomplete product data | Catalogue entry delays launch | Prepare a standardized catalogue early |
| Missing professional content | Public-site presentation is weakened | Use approved temporary brand imagery and replace it later |
| Compressed delivery schedule | Quality or scope may be pressured | Enforce Phase 1 priorities and defer nonessential capabilities |

## Repository structure

```text
golden_touch_beauty/
├── backend/
│   ├── accounts/             # Custom user model and email/phone authentication
│   ├── config/               # Django settings and root URL configuration
│   ├── core/                 # Shared model foundation and health endpoint
│   ├── branches/             # Branch domain app scaffold
│   ├── bookings/             # Booking domain app scaffold
│   ├── customers/            # Customer domain app scaffold
│   ├── services/             # Service catalogue app scaffold
│   ├── products/             # Product catalogue app scaffold
│   ├── inventory/            # Inventory app scaffold
│   ├── orders/               # E-commerce order app scaffold
│   ├── pos/                  # Point-of-sale app scaffold
│   ├── payments/             # Payment app scaffold
│   ├── expenses/             # Expense app scaffold
│   ├── notifications/        # Notification app scaffold
│   ├── reports/              # Reporting app scaffold
│   ├── auditlog/             # Audit-log app scaffold
│   ├── .env.example          # Local environment template
│   ├── manage.py
│   └── requirements.txt
├── docs/
│   ├── Project Requirement Document GTBC.docx
│   └── logo*.png
├── .gitignore
└── README.md
```

The domain apps beyond `accounts` and `core` are currently scaffolds; their models, APIs, workflows, permissions, and tests still need implementation.

## Getting started

### Backend development setup

Prerequisites:

- Python 3.13 or a compatible Python version
- PostgreSQL

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Update `.env` with a secure development secret and valid PostgreSQL credentials, then initialize and run Django:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The development endpoints are:

- Health check: `http://127.0.0.1:8000/api/v1/health/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- Django admin: `http://127.0.0.1:8000/admin/`

Run validation with:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

### Next implementation steps

1. Review and formally approve the PRD and Phase 1 boundary.
2. Resolve open product decisions, especially payment-provider selection and production infrastructure.
3. Collect the business content and catalogue data listed under [Delivery dependencies and risks](#delivery-dependencies-and-risks).
4. Confirm the technical stack and record major choices as architecture decision records.
5. Create UX flows and responsive designs for the public site, customer portal, management console, and offline POS.
6. Establish test, staging, and production environments.
7. Convert the acceptance criteria into traceable user stories and automated test cases as implementation proceeds.

## Documentation

- [Product Requirements Document](docs/Project%20Requirement%20Document%20GTBC.docx) — authoritative requirements, workflows, scope, and acceptance criteria.
- [Brand logo](docs/logo.png) — current repository brand asset.

When this README and the PRD differ, the signed-off PRD and subsequent approved change records should take precedence.
