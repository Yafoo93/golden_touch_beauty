# Golden Touch Beauty Centre Management Platform

<p align="center">
  <img src="docs/logo.png" alt="Golden Touch Beauty Centre logo" width="220">
</p>

<p align="center">
  <strong>Where Beauty Meets Excellence</strong>
</p>

<p align="center">
  A multi-branch beauty business management platform for appointments, e-commerce, point of sale, inventory, customer care, treatment records, payments, and business analytics.
</p>

---

> [!IMPORTANT]
> This project is currently in the **foundation and early implementation stage**.
>
> The repository contains the approved Product Requirements Document, brand assets, Django backend foundations, database structure, API documentation, development seed data, and frontend scaffolding.
>
> Most customer-facing and operational workflows described in this README remain under development unless explicitly marked as implemented.

---

## Overview

The **Golden Touch Beauty Centre Management Platform** is a planned digital system designed to connect the company's public website with its daily business operations.

Customers will be able to:

* Browse beauty services
* Book appointments
* Request home services
* Pay for consultations
* Buy beauty products
* Track orders
* View receipts
* Manage treatment and purchase history
* Save favourite products and services

Staff and management will be able to:

* Manage bookings
* Process sales
* Operate a point-of-sale system
* Monitor stock
* Record treatment information
* Manage expenses
* Approve content
* Review payments
* Generate business reports
* Compare branch performance
* Maintain audit records

The initial deployment covers the **Makola** and **Tse Addo** branches in Accra, Ghana.

The platform is designed to support additional branches without requiring a major redesign.

---

## Business Problem

Golden Touch Beauty Centre currently requires a single source of truth for its customer-facing and internal business operations.

Without an integrated platform, beauty businesses may experience:

* Appointment conflicts
* Duplicate bookings
* Inaccurate stock records
* Difficulty tracking products used during treatments
* Limited visibility across multiple branches
* Inconsistent customer records
* Manual sales and expense reporting
* Difficulty monitoring outstanding balances
* Weak auditability
* Limited customer retention information
* Delays in producing business reports

This platform addresses those challenges by connecting bookings, customers, sales, payments, stock, treatment records, branches, staff actions, and reports within one system.

---

## Project Goals

The project aims to:

* Replace manual appointment, sales, and inventory processes
* Provide one central system for multiple branches
* Improve customer booking and shopping experiences
* Prevent duplicate active bookings
* Track sales, stock, expenses, and appointments by branch
* Reduce stock loss
* Record products consumed during treatments
* Support clinic, consultation, home-service, and bridal workflows
* Improve customer retention
* Protect sensitive treatment information
* Generate reliable daily, weekly, monthly, and branch-level reports
* Preserve a complete audit trail
* Scale to additional branches, services, products, and integrations

---

## Current Project Status

| Area                          | Status                 |
| ----------------------------- | ---------------------- |
| Product Requirements Document | Drafted                |
| Brand identity and logo       | Available              |
| Backend architecture          | Foundation implemented |
| Django project configuration  | Implemented            |
| Custom user model             | Implemented            |
| Branch foundations            | Implemented            |
| Audit foundations             | Implemented            |
| Idempotency foundations       | Implemented            |
| API health endpoint           | Implemented            |
| API documentation             | Implemented            |
| Development seed data         | Implemented            |
| Next.js frontend scaffold     | Implemented            |
| Customer-facing website       | Not yet implemented    |
| Appointment workflows         | Not yet implemented    |
| Online shop                   | Not yet implemented    |
| Point of sale                 | Not yet implemented    |
| Inventory workflows           | Not yet implemented    |
| Payment provider              | Not yet selected       |
| Production deployment         | Not configured         |

---

## Initial Branches

| Branch   | Address                                                    | Operating Hours                      |
| -------- | ---------------------------------------------------------- | ------------------------------------ |
| Makola   | Makola Shopping Mall, Shop 143, Second Floor, Accra, Ghana | Monday–Saturday, 7:30 a.m.–5:00 p.m. |
| Tse Addo | Tse Addo, opposite The Royal Stool Event, Accra, Ghana     | Monday–Saturday, 7:30 a.m.–7:00 p.m. |

Every operational record in the system must be associated with a branch where applicable.

The owner will retain a consolidated cross-branch view.

---

## Brand Direction

* **Primary colours:** Gold, white, and black
* **Style:** Luxurious, modern, glamorous, and professional
* **Primary currency:** Ghana cedis (GHS)
* **Primary language:** English
* **Supported devices:** Desktop, tablet, and mobile browsers
* **POS requirement:** Offline-capable desktop operation

Customer-facing interfaces should remain simple and accessible to users with limited technical experience.

Management interfaces should prioritise speed, clarity, and operational efficiency.

---

## Phase 1 Scope

### Public Website

The public website will include:

* Home
* About
* Services
* Service details
* Appointment booking
* Home-service requests
* Consultation
* Online shop
* Product details
* Cart
* Checkout
* Gallery
* Bridal packages
* Testimonials
* Beauty tips and blog
* Contact
* FAQs
* Policies
* Login
* Registration

Visitors may browse without an account.

Authentication will be required before users can:

* Book appointments
* Purchase products
* Save favourites
* Submit reviews
* Manage account information

---

## Customer Account

Customers will be able to manage:

* Personal profile
* Upcoming appointments
* Pending appointments
* Rescheduled appointments
* Appointment history
* Treatment history
* Consent preferences
* Product orders
* Delivery tracking
* Receipts
* Outstanding balances
* Wishlist
* Saved addresses
* Purchase history
* Reordering
* Before-and-after photograph consent
* Marketing consent

---

## Services and Appointment Management

The platform will support:

* Service categories
* Service descriptions
* Service images
* Service duration
* Branch availability
* Customer eligibility requirements
* Service approval status
* Fixed prices
* Starting prices
* Price ranges
* Selectable pricing options
* Management quotations

A single booking may contain multiple services while preserving separate:

* Durations
* Prices
* Assigned staff
* Treatment information
* Service statuses

### Supported Appointment Types

* Clinic appointments
* Consultations
* Home-service requests
* Group bookings
* Bridal bookings
* Bookings made for another person
* Special-event services
* International home-service requests

### Appointment Management Actions

Authorised staff will be able to:

* Approve appointments
* Reject appointments
* Propose new appointment times
* Reschedule appointments
* Transfer appointments between branches
* Assign staff
* Check in customers
* Mark services in progress
* Complete appointments
* Cancel appointments
* Mark no-shows

---

## Duplicate Booking Prevention

The system should prevent duplicate active bookings for the same customer and service when an earlier booking is:

* Pending
* Confirmed
* Checked in
* In progress
* Rescheduled and awaiting acceptance

An authorised manager may override this restriction only after providing a reason.

The override must be recorded in the audit log.

---

## Consultation Rules

Consultations require a separate non-refundable payment of:

**GHS 200**

A consultation is confirmed only after payment has been verified.

---

## Home-Service Workflow

1. Customer selects eligible services.
2. Customer provides the destination and map location.
3. Customer provides contact details and group size.
4. Customer specifies the event and preferred schedule.
5. Customer provides relevant travel details.
6. Management assigns a branch.
7. Management assesses staffing and travel requirements.
8. Management prepares a complete quotation.
9. Customer accepts the quotation.
10. Customer makes full payment.
11. Management confirms the home service.

Clinic-only treatments must not be offered as home services during Phase 1.

International home services are intended primarily for bridal and special events.

---

## Online Shop

The e-commerce platform will support:

* Product categories
* Product search
* Filters
* Product variants
* Product images
* Wishlist
* Cart
* Checkout
* Verified customer reviews
* Delivery addresses
* Billing addresses
* Clinic pickup
* Delivery orders
* Order tracking
* Reordering
* Preorders
* Return requests

### Preorders

Preorders require full payment.

The customer must be shown an estimated availability date and receive status notifications.

### Returns

Returns must:

* Be requested within 14 days
* Receive management approval
* Meet applicable hygiene and product-condition requirements

Cash on delivery is not included in Phase 1.

---

## Checkout and Stock Reservation

Available stock will be reserved for **30 minutes** while checkout is in progress.

* Successful payment converts the reservation into a stock deduction.
* Failed payment releases the reservation.
* Expired checkout releases the reservation.
* Abandoned checkout releases the reservation.

Delivery orders should be fulfilled from a branch with sufficient available stock.

Clinic pickup should only display branches with adequate stock.

---

## Payments

The platform will support:

* Mobile Money
* Bank transfer
* Online card payments
* Cash at clinic
* Deposits
* Partial payments
* Split payments
* POS payments

Bank-transfer customers may upload proof of payment for management review.

Payments should be allocated to:

* Appointments
* Orders
* Sales
* Consultations
* Home-service quotations

The system must preserve any outstanding balance.

---

## Receipts

Receipts should be:

* Printable
* Downloadable
* Emailed
* Shareable through WhatsApp

Receipts should clearly identify:

* Customer
* Branch
* Items or services
* Payment method
* Amount paid
* Outstanding balance
* Date
* Cashier or responsible staff member
* Transaction reference

---

## Point of Sale

The POS system will support:

* Product sales
* Service sales
* Combined sales
* Walk-in customers
* Split payments
* Deposits
* Partial payments
* Discount controls
* Refunds
* Price changes
* Complimentary services
* Cancellations
* Reversals

Permission-controlled actions must require authorised access.

---

## Offline POS

Each desktop POS installation will be associated with:

* A branch
* A device identifier
* An authorised user session

Offline transactions will receive temporary references.

When connectivity is restored:

1. The transaction is submitted to the server.
2. The server validates the transaction.
3. An official transaction reference is created.
4. Stock is updated.
5. Temporary and official references are linked.
6. Conflicts are flagged for management review.

---

## Inventory Management

The system will maintain inventory separately for each branch.

Inventory features will include:

* Current stock balances
* Reorder levels
* Product batches
* Expiry dates
* Stock receipts
* Sales deductions
* Treatment consumption
* Branch transfers
* Damaged stock
* Expired stock
* Lost stock
* Returned stock
* Stock adjustments
* Physical stock counts
* Preorder allocation

### Inventory Alerts

The platform will generate alerts for:

* Low stock
* Out-of-stock items
* Expiring products
* Expired products
* Available preorder stock
* Stock-count variances

---

## Treatment Consumption

Products used during treatments should be recorded against:

* The service
* The appointment
* The customer
* The responsible staff member
* The branch

Phase 1 will support whole-unit treatment consumption and optional service recipes.

More detailed quantity measurements may be introduced later.

---

## Users and Permissions

| User Type                   | Main Access                                                                               |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| Public visitor              | Browse public content                                                                     |
| Registered customer         | Manage bookings, purchases, payments, receipts, wishlist, addresses, reviews, and consent |
| Owner / Super Administrator | Full cross-branch access                                                                  |
| Branch manager              | Operate assigned branches                                                                 |
| Receptionist                | Manage bookings, check-ins, walk-ins, permitted payments, and receipts                    |
| Sales attendant / Cashier   | Process sales and payments                                                                |
| Stock manager               | Manage stock, transfers, losses, expiry, and counts                                       |
| Service provider            | View assigned appointments and record permitted treatment information                     |

A staff member may:

* Hold multiple roles
* Work at one or more branches
* Receive individual permissions
* Have individual permissions revoked

Sensitive access and permission changes must be recorded in the audit log.

---

## Booking Statuses

Public booking statuses include:

* Pending
* Confirmed
* Checked in
* In progress
* Completed
* Cancelled
* Rescheduled
* No-show

Internal indicators may also represent:

* Payment review
* Proposed time changes
* Quotation review
* Transfer verification
* Awaiting customer acceptance

---

## Completed-Sale Corrections

Completed sales are immutable.

A completed transaction must not be directly edited.

Corrections require:

* Authorised cancellation or reversal
* A reason
* A linked replacement sale where relevant
* A complete audit trail

---

## Reporting and Analytics

The management dashboard will provide information about:

* Appointments
* Booking changes
* Home-service requests
* Sales
* Product revenue
* Service revenue
* Outstanding balances
* Online orders
* Delivery quotations
* Stock
* Expiry
* Expenses
* Pending reviews
* Customer trends
* Branch comparisons
* Payment methods

### Reports

The system will generate reports for:

* Daily sales
* Weekly sales
* Monthly sales
* Product revenue
* Service revenue
* Appointment performance
* Cancellations
* No-shows
* Popular services
* Best-selling products
* Staff sales
* Customer retention
* Inventory
* Expiry
* Expenses
* Product gross profit
* Payments
* Branch comparisons
* Home services
* Online orders
* Consultations

Reports should be exportable as:

* PDF
* Excel
* CSV

---

## Customer Retention Analytics

Retention metrics will include:

* New customers
* Returning customers
* Repeat bookings
* Repeat purchases
* Inactive customers
* Abandoned carts
* Appointment cancellations
* Repeated no-shows
* Favourite services
* Customer lifetime sales value

---

## Financial Calculations

```text
Product gross profit =
Product sales revenue - Cost of goods sold
```

```text
Estimated operating result =
Total recorded revenue
- Product cost of goods sold
- Recorded expenses
```

The operating result must be labelled as an estimate because full service-delivery costing is outside Phase 1.

---

## Security

The planned security baseline includes:

* Secure password hashing
* HTTPS
* Input validation
* Protection against common web attacks
* Role-based access control
* Branch-based access control
* Session timeout
* Login-attempt protection
* Email verification
* Password reset
* Secure object storage
* Payment webhook validation
* Offline synchronisation controls
* Daily backups
* Data export and deletion procedures
* Audit logging

---

## Treatment Data Privacy

Treatment and medical information must be separated from ordinary customer contact information.

Access should be limited to authorised personnel.

Access to sensitive treatment information should be logged.

Treatment photographs require:

* Explicit consent
* Separate consent from marketing permission
* A timestamp
* A stated purpose
* Withdrawal support
* Restricted storage
* Restricted access

---

## Audit Logging

Audit entries should record:

* User
* Role
* Action
* Affected record
* Previous value
* New value
* Branch
* Timestamp
* IP address or device identifier
* Reason, where required

Audit events should include:

* Authentication
* Permission changes
* Pricing changes
* Booking actions
* Stock movements
* Sales
* Refunds
* Treatment-record access
* Consent changes
* Expense changes
* Content approvals
* Branch transfers
* POS synchronisation

---

## Proposed Technology Stack

| Layer           | Technology                                     | Responsibility                                                      |
| --------------- | ---------------------------------------------- | ------------------------------------------------------------------- |
| Backend         | Python, Django, Django REST Framework          | APIs, workflows, authentication, administration, and business rules |
| Database        | PostgreSQL                                     | Transactional data and reporting                                    |
| Frontend        | Next.js                                        | Customer, public, and management interfaces                         |
| Offline POS     | Progressive Web App, Service Worker, IndexedDB | Offline transactions and synchronisation                            |
| Background jobs | Redis and Celery                               | Notifications, reservations, reports, and scheduled processing      |
| File storage    | S3-compatible object storage                   | Images, receipts, proofs, reports, and treatment photographs        |
| Deployment      | Containerised cloud environment                | Scaling, separation, monitoring, and backups                        |
| Payments        | Provider adapter layer                         | Mobile Money, card payments, refunds, and provider switching        |

---

## Core Domain Model

### Identity and Access

* User
* Customer
* Customer Address
* Customer Consent
* Staff Member
* Role
* Permission
* Branch
* Device

### Services and Appointments

* Service Category
* Service
* Service Price Option
* Service Package
* Appointment
* Appointment Service Item
* Appointment History
* Home-Service Request
* Consultation
* Treatment Record
* Treatment Photograph

### Products and Inventory

* Product Category
* Product
* Product Variant
* Product Image
* Product Batch
* Branch Inventory
* Stock Reservation
* Stock Movement
* Stock Count
* Stock Count Item
* Product Recipe

### Commerce

* Shopping Cart
* Cart Item
* Wishlist
* Order
* Order Item
* Delivery Quotation
* Payment
* Payment Allocation
* Invoice
* Receipt
* POS Sale
* POS Sale Item

### Operations

* Expense
* Review
* Notification
* Audit Log
* Content Approval
* Offline Transaction Queue

All relevant records must retain branch attribution.

Transactional records should preserve historical values rather than relying only on current product or service catalogue values.

---

## System Architecture

```text
Public Website / Customer Portal / Management Dashboard
                         │
                         ▼
                    Next.js Frontend
                         │
                         ▼
                Django REST Framework API
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
 Authentication     Business Logic      Reporting
        │                │                 │
        └────────────────┼─────────────────┘
                         ▼
                     PostgreSQL
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
   Redis/Celery    Object Storage      Audit Logs
                         │
                         ▼
                 Payment Providers
```

The offline POS will maintain a local transaction queue and synchronise with the backend when connectivity becomes available.

---

## Repository Structure

```text
golden_touch_beauty/
├── backend/
│   ├── accounts/
│   ├── config/
│   ├── core/
│   ├── branches/
│   ├── bookings/
│   ├── customers/
│   ├── services/
│   ├── products/
│   ├── inventory/
│   ├── orders/
│   ├── pos/
│   ├── payments/
│   ├── expenses/
│   ├── notifications/
│   ├── reports/
│   ├── auditlog/
│   ├── .env.example
│   ├── manage.py
│   └── requirements.txt
├── frontend/
├── docs/
│   ├── Project Requirement Document GTBC.docx
│   ├── DEVELOPMENT_ROADMAP.md
│   ├── PHASE_1_BUILD_CHECKLIST.md
│   ├── BUSINESS_SEED_DATA.md
│   ├── DRAFT_POLICIES.md
│   ├── API_CONVENTIONS.md
│   ├── architecture/
│   └── logo.png
├── compose.yaml
├── .gitignore
└── README.md
```

Most domain applications currently contain scaffolding and still require full implementation of:

* Models
* APIs
* Permissions
* Workflows
* Validation
* Tests

---

## Local Development

### Requirements

* Python 3.13 or a compatible Python version
* PostgreSQL
* Docker
* Node.js and npm for frontend development

### Backend Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Start PostgreSQL from the repository root:

```powershell
docker compose up -d postgres
```

Update the `.env` file with an appropriate development secret.

Then run:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_development_data
python manage.py runserver
```

Run the durable email worker in a second terminal:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python manage.py process_email_jobs
```

The same worker also schedules and delivers customer appointment reminders 24
hours and 6 hours before confirmed appointments. It reconciles existing future
bookings every five minutes, and reminder jobs are invalidated automatically
when an appointment is cancelled, completed, or moved to a different time.

The web process queues booking, order, receipt, password-reset, and
email-verification messages in PostgreSQL. The worker delivers them outside
the web request and retries temporary failures with exponential backoff. On
Render, create a Background Worker from the same repository and backend root
with this start command:

```text
python manage.py process_email_jobs
```

Give the worker the same `DATABASE_URL` and email environment variables as the
backend web service. Do not enable `EMAIL_JOBS_EAGER` in production.

The seed command loads:

* Makola branch
* Tse Addo branch
* Development service catalogue
* Development product catalogue
* Product variants
* Branch availability
* Opening stock

---

## Development Endpoints

* Health check: `http://127.0.0.1:8000/api/v1/health/`
* OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
* Swagger UI: `http://127.0.0.1:8000/api/docs/`
* ReDoc: `http://127.0.0.1:8000/api/redoc/`
* Django admin: `http://127.0.0.1:8000/admin/`

---

## Testing

Run:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --settings=config.settings.test
```

Future testing should cover:

* Authentication
* Role permissions
* Branch isolation
* Booking conflicts
* Payment allocation
* Stock reservation
* Inventory deductions
* POS synchronisation
* Treatment privacy
* Audit logging
* Reports
* Refund and reversal workflows

---

## Roadmap

### Phase 1

* Responsive public website
* Customer accounts
* Appointment booking
* Home-service requests
* Paid consultations
* Online shop
* Payments
* Receipts
* POS
* Offline operations
* Branch inventory
* Treatment records
* Expenses
* Essential reports
* Content approvals
* Roles and permissions
* Notifications
* Audit logs

### Phase 2

* Staff schedules
* Attendance
* Leave
* Salaries
* Advanced capacity planning
* Automatic staff assignment
* Advanced service costing
* Complete service-profit analysis
* WhatsApp Business API
* Supplier management
* Purchase orders
* Goods received
* Supplier payments
* Barcode generation and scanning
* Detailed product-consumption measurements

### Phase 3

* Native mobile applications
* Loyalty points
* Referral programmes
* Gift cards
* Automated subscriptions
* Recurring beauty-plan billing
* Discount codes
* Courier integrations
* Dynamic international shipping
* Multi-currency display
* Waiting lists
* Customer reference-image upload
* Advanced forecasting
* Demand prediction
* Staff performance analytics
* Central warehouse management

---

## Phase 1 Acceptance Checklist

* [x] Public visitors can browse available services and products
* [ ] Customers can register and log in with email or phone credentials
* [ ] Customers can book multiple services under one reference
* [ ] Customers can select either Makola or Tse Addo
* [ ] Customers can request preferred appointment times
* [ ] Customers can select Pay at Clinic
* [ ] Consultations require a non-refundable GHS 200 payment
* [ ] Management can approve bookings
* [ ] Management can propose appointment changes
* [ ] Customers can accept proposed changes
* [ ] Duplicate active bookings are prevented
* [ ] Management overrides are audited
* [ ] Home-service quotations are supported
* [ ] Customers can purchase products online
* [ ] Preorders require full payment
* [ ] Checkout reserves stock for 30 minutes
* [ ] Successful payments deduct stock
* [ ] Pickup reflects branch availability
* [ ] POS supports products and services
* [ ] POS supports split payments
* [ ] Offline POS transactions synchronise later
* [ ] Every sale records the branch and cashier
* [ ] Inventory is branch-specific
* [ ] Treatment consumption updates inventory
* [ ] Physical stock counts are supported
* [ ] Low-stock and expiry alerts are generated
* [ ] Completed sales are immutable
* [ ] Corrections use audited reversals
* [ ] Customers receive receipts
* [ ] Sensitive treatment information is restricted
* [ ] Publication changes require approval
* [ ] Reports export to PDF, Excel, and CSV
* [ ] Branch comparison reports are available
* [ ] Complete audit logs are maintained
* [ ] Interfaces work on desktop and mobile browsers

---

## Delivery Dependencies

The following business inputs are required:

* Final service catalogue
* Service descriptions
* Service durations
* Service prices
* Service photographs
* Product catalogue
* Product variants
* Product cost prices
* Product selling prices
* Opening stock
* Product batches
* Expiry dates
* Product images
* Staff list
* Branch contact information
* Bank details
* Mobile Money details
* Payment-provider decision
* Legal policies
* Gallery content
* Social links
* Email accounts
* Hosting decision
* Domain configuration

---

## Key Risks

| Risk                              | Potential Impact                     | Mitigation                                                        |
| --------------------------------- | ------------------------------------ | ----------------------------------------------------------------- |
| Payment-provider approval delays  | Online payments may be delayed       | Begin onboarding early and retain bank transfer and Pay at Clinic |
| Offline inventory conflicts       | Online and offline stock may differ  | Use branch stock controls, queues, alerts, and permissions        |
| Incomplete catalogue data         | Public launch may be delayed         | Prepare standardised business data early                          |
| Missing professional content      | Public website may appear incomplete | Use approved temporary assets and replace them later              |
| Compressed development schedule   | Scope or quality may suffer          | Enforce Phase 1 priorities and defer nonessential features        |
| Sensitive treatment data exposure | Privacy and reputational damage      | Use permissions, encryption, secure storage, and access logs      |

---

## Documentation

* [Product Requirements Document](docs/Project%20Requirement%20Document%20GTBC.docx)
* [Development Roadmap](docs/DEVELOPMENT_ROADMAP.md)
* [Phase 1 Build Checklist](docs/PHASE_1_BUILD_CHECKLIST.md)
* [Development Business Seed Data](docs/BUSINESS_SEED_DATA.md)
* [Draft Policies](docs/DRAFT_POLICIES.md)
* [Authentication Architecture Decision](docs/architecture/ADR-001-authentication.md)
* [API Conventions](docs/API_CONVENTIONS.md)
* [Brand Logo](docs/logo.png)

Where this README differs from an approved and signed Product Requirements Document or subsequent approved change record, the approved requirements should take precedence.

---

## Current Priorities

1. Approve the Phase 1 requirements and scope.
2. Select a payment provider.
3. Complete business catalogue data.
4. Create UX designs.
5. Implement authentication workflows.
6. Implement customer and staff permissions.
7. Build the service catalogue.
8. Build appointment workflows.
9. Build products and inventory.
10. Implement payments and POS.
11. Configure test, staging, and production environments.
12. Convert acceptance criteria into automated tests.

---

## Disclaimer

This repository documents and develops a business-management platform for Golden Touch Beauty Centre.

Features described as planned, proposed, future, or Phase 1 are not necessarily available in the current application.

The platform should not be deployed for production financial, treatment, inventory, or customer-data operations until the relevant workflows, security controls, tests, policies, and deployment configurations have been completed and approved.

---

## Author and Product Team

**Product:** Golden Touch Beauty Centre Management Platform
**Business:** Golden Touch Beauty Centre
**Technical Development:** Kastech Inc.

### Lead Developer

**Kassim Mutawakil**

Software Engineer | AI Researcher | Cybercrime Investigator

* GitHub: https://github.com/Yafoo93
* LinkedIn: https://linkedin.com/in/mutawakil-kassim-159a7178
* Email: [kassim.mutawakil@gmail.com](mailto:kassim.mutawakil@gmail.com)
