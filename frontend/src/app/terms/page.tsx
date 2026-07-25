import type { Metadata } from "next";

import {
  PolicyLayout,
  type PolicySection,
} from "@/components/legal/policy-layout";

export const metadata: Metadata = {
  title: "Terms and Conditions",
  description:
    "Development-draft terms governing use of the Golden Touch Beauty Centre website, accounts, bookings, services, payments, and product orders.",
};

const sections: PolicySection[] = [
  {
    id: "agreement",
    title: "Agreement to these terms",
    content: (
      <>
        <p>
          These sample Terms and Conditions govern access to and use of the
          Golden Touch Beauty Centre website, customer accounts, booking tools,
          product shop, and related online services. References to “Golden
          Touch,” “we,” “us,” or “our” mean the business entity identified in
          the final approved version.
        </p>
        <p>
          By creating an account, submitting a booking or order, or otherwise
          using the platform, you agree to the version of these terms presented
          to you. If you do not agree, do not use the affected service.
        </p>
      </>
    ),
  },
  {
    id: "accounts",
    title: "Customer accounts",
    content: (
      <>
        <p>
          You must provide accurate, current information and update it when it
          changes. You are responsible for protecting your password and for
          activity performed through your account unless you promptly report
          suspected unauthorized access.
        </p>
        <p>
          We may request verification, restrict access, or suspend an account
          where reasonably necessary to protect customers, the business, or the
          platform from misuse, fraud, or security threats.
        </p>
      </>
    ),
  },
  {
    id: "services",
    title: "Service information and suitability",
    content: (
      <>
        <p>
          Service descriptions, durations, images, and prices are provided for
          general information and may be updated. Actual recommendations and
          results depend on individual needs, consultation, suitability, staff
          availability, and the selected branch.
        </p>
        <p>
          Beauty and skincare information does not replace medical advice.
          Customers should disclose relevant allergies, medication, pregnancy,
          health conditions, recent procedures, and previous reactions.
          Golden Touch may decline, postpone, or modify a service where it may
          be unsuitable or where professional medical assessment is advisable.
        </p>
      </>
    ),
  },
  {
    id: "bookings",
    title: "Bookings and branch availability",
    content: (
      <>
        <p>
          A submitted date or time is not guaranteed until the booking reaches
          the confirmation status defined by the final operating policy.
          Services and appointment times may differ between Makola, Tse Addo,
          and any future branches.
        </p>
        <p>
          You must arrive at the agreed location and time with information
          required for the service. Late arrival may reduce available service
          time or require rescheduling, subject to the approved cancellation
          and refund policy.
        </p>
      </>
    ),
  },
  {
    id: "prices-payments",
    title: "Prices and payments",
    content: (
      <>
        <p>
          Prices are displayed in the applicable currency and should be
          reviewed before payment. Services require full payment using an
          available online or clinic payment method. A booking or order is not
          treated as paid until payment has been successfully verified.
        </p>
        <p>
          Online payments may be processed by an approved third-party payment
          provider. Golden Touch must not store raw card numbers or card
          security codes. Bank, network, or provider delays may affect
          confirmation, and duplicate or disputed payments will be investigated
          against transaction records.
        </p>
      </>
    ),
  },
  {
    id: "products",
    title: "Products, stock, and fulfilment",
    content: (
      <>
        <p>
          Product orders remain subject to current price, stock, payment, and
          fulfilment confirmation. Branch pickup is available only where the
          selected branch has sufficient eligible stock for the complete order.
        </p>
        <p>
          Packaging and appearance may change and may differ slightly from
          photography. Product directions and warnings should be followed.
          Golden Touch may cancel and appropriately refund an order that cannot
          be fulfilled, subject to the approved delivery and returns policy.
        </p>
      </>
    ),
  },
  {
    id: "acceptable-use",
    title: "Acceptable use",
    content: (
      <>
        <p>You must not use the platform to:</p>
        <ul>
          <li>Break applicable law or infringe another person’s rights.</li>
          <li>Submit false, fraudulent, abusive, or harmful information.</li>
          <li>Attempt unauthorized access to accounts, data, or systems.</li>
          <li>Interfere with platform security, availability, or operation.</li>
          <li>
            Copy, scrape, resell, or misuse content or services without
            authorization.
          </li>
        </ul>
      </>
    ),
  },
  {
    id: "intellectual-property",
    title: "Intellectual property",
    content: (
      <p>
        The Golden Touch name, branding, website design, text, graphics,
        photographs, and software are owned by Golden Touch or used with
        permission unless stated otherwise. You may use the platform for
        personal, lawful purposes but may not reproduce or commercially exploit
        protected material without written authorization.
      </p>
    ),
  },
  {
    id: "third-parties",
    title: "Third-party services and links",
    content: (
      <p>
        The platform may link to maps, payment providers, messaging services,
        social networks, or other third parties. Their systems and policies are
        outside our control. A link does not automatically mean that Golden
        Touch endorses every third-party statement, product, or practice.
      </p>
    ),
  },
  {
    id: "availability",
    title: "Platform availability",
    content: (
      <p>
        We aim to keep the platform accurate and available but cannot promise
        uninterrupted or error-free operation. Maintenance, network failure,
        security response, provider outages, and events outside reasonable
        control may temporarily affect features. We may correct errors and
        update or withdraw features where reasonably necessary.
      </p>
    ),
  },
  {
    id: "liability",
    title: "Responsibility and liability",
    content: (
      <>
        <p>
          Customers are responsible for providing accurate information,
          following reasonable preparation and aftercare instructions, and
          seeking appropriate medical attention where required.
        </p>
        <p>
          The final legal version may contain reasonable limitations of
          liability permitted by applicable law. Nothing in these sample terms
          is intended to exclude liability or consumer rights that cannot
          lawfully be excluded under Ghanaian law.
        </p>
      </>
    ),
  },
  {
    id: "changes-law-contact",
    title: "Changes, governing law, and contact",
    content: (
      <>
        <p>
          We may update these terms to reflect changes in law, operations,
          services, or security. Material changes should be communicated and,
          where required, accepted before continued use of an affected feature.
        </p>
        <p>
          The approved terms are expected to be governed by the laws of Ghana,
          with the final dispute-resolution wording and business identity to be
          supplied by legal counsel. Until an official legal email is
          available, customers may use the branch contacts shown on the Contact
          page.
        </p>
      </>
    ),
  },
];

export default function TermsPage() {
  return (
    <PolicyLayout
      eyebrow="Golden Touch policies"
      title="Terms and Conditions"
      description="Provisional terms for accounts, bookings, beauty services, payments, products, and use of the Golden Touch platform."
      status="This sample is provided for development and testing only. It has not been approved by legal counsel and must be replaced or formally approved before production launch."
      sections={sections}
    />
  );
}
