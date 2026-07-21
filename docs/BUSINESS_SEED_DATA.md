# Golden Touch Beauty Centre — Development Seed Data

Status: **Approved for development and testing only**

This document provides the initial content to use while building the website, booking system, shop, management dashboard, and POS. Placeholder prices, costs, quantities, descriptions, images, statistics, and testimonials must be reviewed before production launch.

The data is implemented by `python manage.py seed_development_data`. The command is safe to rerun: it updates the named development branch/catalogue records without duplicating them and does not reset an existing branch inventory quantity.

## Data rules

- Currency: Ghana cedis (GHS/GH₵).
- The PRD remains authoritative for system behavior.
- Both branches are active in Phase 1.
- Services and products are initially available at both branches.
- Administrators must be able to enable or disable every service, product, or product variant separately for each branch.
- Stock quantities are tracked separately for Makola and Tse Addo.
- Service prices, product prices, product costs, stock, and descriptions below are development placeholders unless explicitly identified as confirmed.
- Development images in `frontend/public/images` may be replaced before production.
- Unverified ratings, testimonials, and business statistics may remain during development but must be removed or replaced with verified information before production.

## Branches

### Makola

| Field | Value |
| --- | --- |
| Code | `MAKOLA` |
| Address | Makola Shopping Mall, Shop 143, Second Floor, Accra, Ghana |
| Primary contact/WhatsApp | `+233 24 137 0429` |
| Secondary contact/WhatsApp | `+233 25 771 1182` |
| Email | Not available yet |
| Opening days | Monday–Saturday |
| Opening time | 7:30 a.m. |
| Closing time | 5:00 p.m. |
| Map | [Google Maps location](https://maps.google.com/maps?vet=10CAAQoqAOahcKEwj4mrSs7c-VAxUAAAAAHQAAAAAQIg..i&pvq=CgwvZy8xaGRfbDdmN2Q&fvr=1&cs=0&um=1&ie=UTF-8&fb=1&gl=gh&sa=X&ftid=0xfdf90bdedf8501b:0x52470e6bd2670358) |
| Status | Active |

### Tse Addo

| Field | Value |
| --- | --- |
| Code | `TSE_ADDO` |
| Address | Tse Addo, opposite The Royal Stool Event, Accra, Ghana |
| Primary contact/WhatsApp | `+233 24 137 0429` |
| Secondary contact/WhatsApp | `+233 20 791 1043` |
| Email | Not available yet |
| Opening days | Monday–Saturday |
| Opening time | 7:30 a.m. |
| Closing time | 7:00 p.m. |
| Map | Not available yet |
| Status | Active |

Until branch email addresses are supplied, the website should hide the email field rather than display a false or empty address.

## Service categories

1. Skin and Clinical Aesthetics
2. Hair and Bridal/Glam
3. Full-Body Treatment
4. Face and Body Products

“Face and Body Products” is retained because it appears in the PRD service catalogue. It may link customers to relevant shop products rather than behave as a bookable treatment category.

## Development service catalogue

All listed services are initially enabled at Makola and Tse Addo. Prices and durations are placeholders. Management must be able to change them without developer involvement.

| Service | Category | Development description | Placeholder price | Placeholder duration | Image |
| --- | --- | --- | ---: | ---: | --- |
| Facial Treatment | Skin and Clinical Aesthetics | A personalized facial designed to cleanse, exfoliate, hydrate, and refresh the skin. The final treatment steps and products should be selected after assessing the customer’s skin needs. | GH₵250 | 60 min | `/images/facial_treatment.jpeg` |
| Sunburn Treatment | Skin and Clinical Aesthetics | A soothing skin-care treatment intended to calm the appearance of sun-stressed skin, support hydration, and improve comfort. Customers with severe burns or medical symptoms should be referred to a qualified medical professional. | GH₵220 | 60 min | `/images/sunburn.jpeg` |
| Acne Treatment | Skin and Clinical Aesthetics | A targeted skin-care session for acne-prone skin, focusing on gentle cleansing, congestion management, hydration, and an appropriate home-care recommendation. Results vary and medical acne may require clinical referral. | GH₵280 | 60 min | `/images/acne.jpeg` |
| Hyperpigmentation and Dark-Spot Treatment | Skin and Clinical Aesthetics | A tailored treatment that supports a brighter, more even-looking complexion while addressing the appearance of dark marks. Treatment selection depends on skin assessment and sensitivity. | GH₵320 | 90 min | `/images/dark_spot.jpeg` |
| Skin-Tag Removal | Skin and Clinical Aesthetics | A consultation-led procedure for suitable skin tags, performed only after the treatment provider assesses eligibility, location, and relevant medical considerations. | GH₵300 | 60 min | `/images/skintag.jpeg` |
| Chemical-Burn Treatment | Skin and Clinical Aesthetics | A specialist consultation and restorative care plan for skin affected by chemical irritation or burns. Active, severe, or medically urgent burns must be referred for appropriate medical care. | GH₵400 | 120 min | `/images/burns_treatment.jpeg` |
| Tattoo Removal | Skin and Clinical Aesthetics | A consultation-led tattoo-removal service. The recommended approach, number of sessions, suitability, and expected outcome depend on tattoo and skin characteristics. | GH₵600 | 120 min | `/images/tattoo.jpeg` |
| Hair Treatment | Hair and Bridal/Glam | A hair and scalp care session selected for the customer’s hair condition and goals, followed by suitable conditioning and finishing recommendations. | GH₵300 | 120 min | `/images/hair_treatment.jpeg` |
| Hair Styling | Hair and Bridal/Glam | Professional hair preparation and styling based on the requested look, hair condition, length, and selected finishing requirements. Final pricing may vary by style and materials. | GH₵250 | 120 min | `/images/hair_treatment.jpeg` |
| Bridal Makeup and Styling | Hair and Bridal/Glam | A bridal beauty service combining consultation, complexion preparation, makeup, and agreed styling for the wedding look. Group size, location, travel, and package content may change the final quotation. | GH₵800 | 120 min | `/images/bridal.jpeg` |
| Makeup Artistry | Hair and Bridal/Glam | Professional makeup tailored to the customer’s features, skin needs, event, and preferred finish. Product selection and intensity are agreed during the appointment. | GH₵350 | 90 min | `/images/makeup.jpeg` |
| Gele Styling | Hair and Bridal/Glam | Professional gele or head-wrap styling shaped to complement the customer’s outfit, event, and preferred look. Material complexity may affect the final price and duration. | GH₵200 | 60 min | `/images/gele.jpeg` |
| Full-Body Treatment | Full-Body Treatment | A consultation-led full-body beauty and wellness treatment tailored to the customer’s needs. Specific treatment options, exclusions, products, and pricing must be finalized by management. | GH₵500 | 120 min | `/images/hero2.jpeg` |

### Service payment rule

- Full payment is required.
- A customer may pay online or select Pay at Clinic.
- Online-payment confirmation occurs only after verified payment.
- A Pay at Clinic booking is created as **Pending**, following the PRD, until management confirms the requested appointment.
- Management can change prices, durations, payment options, and branch availability.

### Medical-content caution

Development descriptions are general commercial copy, not medical diagnoses, guarantees, or clinical instructions. Golden Touch management and an appropriately qualified treatment professional must review clinical claims, contraindications, consent wording, and aftercare information before publication.

## Product categories

1. Marcelito Face and Body Products — Golden Touch house brand
2. Face Creams
3. Face Serums and Oils
4. Body Creams
5. Body Serums and Oils
6. Body and Face Soap

## Development product catalogue

All products are initially enabled at both branches. Each product starts with one “Standard” variant. Prices, costs, SKUs, stock, descriptions, sizes, ingredients, benefits, and images require management review before production.

| Product | Category | Development description | SKU | Variant | Selling price | Cost price | Makola stock | Tse Addo stock | Image |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Marcelito Face Cream | Marcelito Face and Body Products | A daily face moisturizer from the Golden Touch house range, intended to support soft, comfortable, hydrated-looking skin. Final ingredients, skin suitability, directions, and claims must match the supplied product label. | `MRC-FC-STD` | Standard | GH₵180 | GH₵100 | 20 | 20 | `/images/face_cream.jpeg` |
| Marcelito Face Serum and Oil | Marcelito Face and Body Products | A concentrated face-care product intended to complement a daily moisturizing routine and support a smooth, nourished appearance. Final usage and claims must follow the approved formula and label. | `MRC-FSO-STD` | Standard | GH₵160 | GH₵90 | 20 | 20 | `/images/syrum_n_oil.jpeg` |
| Marcelito Body Cream | Marcelito Face and Body Products | A moisturizing body cream from the Golden Touch house range, developed for everyday hydration and softer-feeling skin. Final ingredient and suitability information must be supplied. | `MRC-BC-STD` | Standard | GH₵200 | GH₵115 | 20 | 20 | `/images/body_cream.jpeg` |
| Marcelito Body Serum and Oil | Marcelito Face and Body Products | A body-care serum and oil product intended to help seal in moisture and leave the skin feeling smooth. Final directions and claims must match the approved product documentation. | `MRC-BSO-STD` | Standard | GH₵190 | GH₵105 | 20 | 20 | `/images/body_syrum_oil.jpeg` |
| Marcelito Body and Face Soap | Marcelito Face and Body Products | A cleansing bar or wash from the Golden Touch house range for the body and, where the final formula permits, the face. Suitability and directions must follow the approved label. | `MRC-BFS-STD` | Standard | GH₵100 | GH₵55 | 20 | 20 | `/images/body_n_face_soap.jpeg` |
| Face Cream | Face Creams | A general facial moisturizer intended to support everyday hydration. The final listing must identify the actual brand, size, ingredients, directions, skin types, and warnings. | `GEN-FC-STD` | Standard | GH₵150 | GH₵85 | 20 | 20 | `/images/face_cream.jpeg` |
| Face Serum and Oil | Face Serums and Oils | A facial serum or oil for use as part of a suitable skin-care routine. The production listing must use the actual product name, formula, size, directions, and claims. | `GEN-FSO-STD` | Standard | GH₵140 | GH₵75 | 20 | 20 | `/images/syrum_n_oil.jpeg` |
| Body Cream | Body Creams | An everyday body moisturizer intended to help keep skin feeling soft and hydrated. Actual brand, formula, size, usage, and warnings must be added before production. | `GEN-BC-STD` | Standard | GH₵170 | GH₵95 | 20 | 20 | `/images/body_cream1.jpeg` |
| Body Serum and Oil | Body Serums and Oils | A moisturizing body serum or oil intended to complement daily body care. The final listing must reflect the actual product formula and approved claims. | `GEN-BSO-STD` | Standard | GH₵160 | GH₵90 | 20 | 20 | `/images/body_syrum_oil.jpeg` |
| Body and Face Soap | Body and Face Soap | A cleansing product for body use and, only where the actual formula permits, facial use. Final skin suitability, directions, ingredients, and warnings must be supplied. | `GEN-BFS-STD` | Standard | GH₵80 | GH₵40 | 20 | 20 | `/images/body_n_face_soap.jpeg` |

### Product management requirements

- Management can select the branches where each product and variant is sold.
- Each branch has an independent stock quantity, reorder level, batch, and expiry information where applicable.
- Product selling prices remain consistent across branches in the initial phase, as required by the PRD.
- Cost prices and profit information are restricted to authorized management users.
- Public product claims must be supported by the real packaging/formulation before production.

## Payment provider

Selected provider: **Korapay** (`korapay.com`)

Development must still confirm and document:

- Account approval and supported Ghana settlement arrangement.
- Ghana Mobile Money support.
- Card support and international-payment behavior.
- Supported currencies and settlement currency.
- Fees and settlement timing.
- Refund and reversal support.
- Hosted checkout or secure provider component.
- Webhook signature verification and retry behavior.
- Sandbox and production credentials.

The integration must use the platform’s payment-adapter interface. No raw card number, CVV, or expiry field may be handled or stored by Golden Touch application servers.

## Policy content

Draft development policies are stored in [DRAFT_POLICIES.md](DRAFT_POLICIES.md). They are placeholders requiring business and appropriate legal review before production.

## Outstanding information

- [ ] Email address for Makola.
- [ ] Email address for Tse Addo.
- [ ] Google Maps link for Tse Addo.
- [ ] Final service prices and exact durations.
- [ ] Treatment professional review of clinical descriptions, contraindications, and consent wording.
- [ ] Final product brands, sizes, ingredients, directions, warnings, SKUs, variants, prices, costs, batches, expiry dates, and opening stock.
- [ ] Korapay merchant approval, supported methods, and credentials.
- [ ] Verified ratings, testimonials, and business statistics—or approval to remove them.
- [ ] Commercial-use approval or replacement for every development image.
- [ ] Approved production policies.
