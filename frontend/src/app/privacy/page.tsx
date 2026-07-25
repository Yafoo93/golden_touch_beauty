import type { Metadata } from "next";

import {
  PolicyLayout,
  type PolicySection,
} from "@/components/legal/policy-layout";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "Development-draft privacy policy explaining how Golden Touch Beauty Centre may collect, use, protect, retain, and share personal information.",
};

const sections: PolicySection[] = [
  {
    id: "scope-controller",
    title: "Scope and data controller",
    content: (
      <>
        <p>
          This sample policy explains how Golden Touch Beauty Centre may handle
          personal data when people use the website, create accounts, contact a
          branch, book services, make payments, purchase products, or interact
          with staff.
        </p>
        <p>
          The final policy must identify the registered Golden Touch legal
          entity acting as data controller, its physical address, registration
          details, privacy contact, and any required Data Protection Commission
          registration information.
        </p>
      </>
    ),
  },
  {
    id: "information-collected",
    title: "Information we may collect",
    content: (
      <>
        <p>Depending on the service used, information may include:</p>
        <ul>
          <li>
            Identity and contact details, such as name, email address, telephone
            number, delivery address, and account identifiers.
          </li>
          <li>
            Account and security information, including password hashes,
            verification status, session records, device information, and
            security events.
          </li>
          <li>
            Booking details, including selected branch, service, date, time,
            notes, status, and attendance history.
          </li>
          <li>
            Treatment-relevant information voluntarily supplied for suitability
            and safety, such as allergies, medication, pregnancy, conditions,
            previous procedures, and reactions.
          </li>
          <li>
            Order, product, pickup, delivery, payment-status, refund, receipt,
            and transaction-reference information.
          </li>
          <li>
            Communications, consent choices, complaints, feedback, and customer
            support records.
          </li>
          <li>
            Technical information such as IP address, browser, device, request
            identifiers, logs, and website interaction data.
          </li>
        </ul>
      </>
    ),
  },
  {
    id: "collection-sources",
    title: "How information is collected",
    content: (
      <p>
        Information may be collected directly from you through forms,
        accounts, booking and checkout steps, branch communications, and
        consultations. It may also be generated through platform use or
        received from authorized staff, payment providers, delivery providers,
        security services, and other parties involved in fulfilling your
        request. Where information comes from another source, required privacy
        information should be provided as soon as reasonably practicable.
      </p>
    ),
  },
  {
    id: "purposes",
    title: "Why information may be used",
    content: (
      <>
        <p>Golden Touch may process information to:</p>
        <ul>
          <li>Create, verify, secure, and support customer accounts.</li>
          <li>
            Assess requests, arrange appointments, and provide suitable beauty
            services.
          </li>
          <li>
            Process orders, payments, branch pickup, delivery, receipts,
            cancellations, and refunds.
          </li>
          <li>
            Communicate confirmations, reminders, service updates, security
            notices, and customer-support responses.
          </li>
          <li>
            Manage branches, inventory, staff permissions, reporting, audit
            trails, fraud prevention, and platform security.
          </li>
          <li>
            Meet legal, accounting, regulatory, insurance, and dispute-handling
            obligations.
          </li>
          <li>
            Send optional marketing only where an appropriate choice or consent
            permits it.
          </li>
        </ul>
      </>
    ),
  },
  {
    id: "lawful-processing",
    title: "Basis for processing",
    content: (
      <p>
        The final approved policy must map each processing activity to an
        appropriate basis under Ghanaian law. Depending on the context, this
        may include providing a requested service or contract, consent,
        compliance with legal obligations, protection of legitimate business
        and security interests, or protection of a person’s vital interests.
        Treatment-relevant or otherwise sensitive information requires
        particular care and an appropriate legal basis.
      </p>
    ),
  },
  {
    id: "payments",
    title: "Payment information",
    content: (
      <p>
        Online payment details may be submitted directly to an approved payment
        provider such as Korapay. Golden Touch should receive only the
        transaction details needed to verify and reconcile payment. Golden
        Touch must not store raw card numbers, card security codes, or payment
        credentials that should remain with the payment provider.
      </p>
    ),
  },
  {
    id: "sharing",
    title: "Sharing and service providers",
    content: (
      <>
        <p>
          Information may be shared only where necessary with authorized Golden
          Touch staff and service providers supporting payments, hosting,
          email, messaging, storage, analytics, security, professional advice,
          delivery, or customer support. Access should be limited to the
          information required for the relevant task.
        </p>
        <p>
          Information may also be disclosed where required by law, a valid
          regulatory or court process, the protection of rights or safety, or a
          properly managed business transaction. Golden Touch should not sell
          personal information as a customer-data product.
        </p>
      </>
    ),
  },
  {
    id: "international-transfers",
    title: "International data transfers",
    content: (
      <p>
        Some approved technology providers may process or store information
        outside Ghana. Before production, Golden Touch must identify these
        providers and ensure that any international transfer uses safeguards
        required by applicable Ghanaian data-protection law and the final
        legal review.
      </p>
    ),
  },
  {
    id: "retention",
    title: "Data retention",
    content: (
      <p>
        Information should be retained only as long as reasonably necessary for
        the stated purpose and applicable legal, accounting, security,
        insurance, dispute, and regulatory requirements. Different records may
        require different periods. The final policy must include or reference
        an approved retention schedule and explain when information is deleted,
        anonymized, or securely archived.
      </p>
    ),
  },
  {
    id: "security",
    title: "Security safeguards",
    content: (
      <p>
        Golden Touch uses or plans to use measures such as password hashing,
        secure server sessions, HTTP-only cookies, CSRF protection, access
        controls, branch-based permissions, audit logging, validation,
        monitoring, backups, and provider security controls. No internet or
        storage system is completely risk-free. Suspected incidents should be
        investigated and reported where applicable law requires notification.
      </p>
    ),
  },
  {
    id: "cookies",
    title: "Cookies and similar technologies",
    content: (
      <p>
        The platform uses essential cookies for secure sessions, authentication,
        CSRF protection, and necessary website operation. Any future analytics,
        advertising, or non-essential technologies must be documented and,
        where required, offered through an appropriate consent choice before
        deployment.
      </p>
    ),
  },
  {
    id: "marketing",
    title: "Marketing choices",
    content: (
      <p>
        Marketing consent is optional and separate from necessary account,
        booking, payment, order, security, and service communications. A person
        may withdraw future direct-marketing consent using the available
        unsubscribe or privacy-contact method. Withdrawal does not affect
        processing already lawfully completed.
      </p>
    ),
  },
  {
    id: "rights",
    title: "Your privacy rights",
    content: (
      <>
        <p>
          Subject to applicable conditions and exceptions, rights under
          Ghana’s Data Protection Act, 2012 (Act 843) may include being informed
          about processing, requesting access to personal data, objecting to
          specified processing, correcting inaccurate information, and
          requiring direct marketing to stop. Additional rights and procedures
          must be confirmed by legal counsel in the final policy.
        </p>
        <p>
          Golden Touch may need to verify identity before acting on a request.
          Individuals may also raise concerns with Ghana’s Data Protection
          Commission where they believe personal data has been mishandled.
        </p>
      </>
    ),
  },
  {
    id: "children",
    title: "Children’s information",
    content: (
      <p>
        The final policy and service rules must define age requirements and the
        circumstances in which parent or guardian involvement is required.
        Golden Touch should not knowingly collect children’s information
        through services that are not approved for them. Any necessary
        processing must follow applicable consent, safety, and data-protection
        requirements.
      </p>
    ),
  },
  {
    id: "changes-contact",
    title: "Policy changes and contact",
    content: (
      <>
        <p>
          This policy may be updated when practices, providers, laws, or
          services change. Material changes should be communicated
          appropriately, and the current approved version and effective date
          should remain available.
        </p>
        <p>
          The final version must provide the official privacy email, physical
          address, responsible contact, request procedure, response process, and
          Data Protection Commission complaint information. Until then,
          customers may use the branch contacts shown on the Contact page.
        </p>
      </>
    ),
  },
];

export default function PrivacyPage() {
  return (
    <PolicyLayout
      eyebrow="Golden Touch policies"
      title="Privacy Policy"
      description="How Golden Touch may collect, use, share, protect, and retain personal information across accounts, bookings, treatments, payments, and orders."
      status="This sample is for development and testing only. It requires review against Golden Touch’s actual data practices, providers, retention schedule, registrations, and legal obligations before production launch."
      sections={sections}
    />
  );
}
