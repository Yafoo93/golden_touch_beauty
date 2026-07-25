import type { Metadata } from "next";

import {
  PolicyLayout,
  type PolicySection,
} from "@/components/legal/policy-layout";

export const metadata: Metadata = {
  title: "Booking Cancellation and Refund Policy",
  description:
    "Development-draft policy for Golden Touch appointment cancellations, rescheduling, no-shows, and service-payment refunds.",
};

const sections: PolicySection[] = [
  {
    id: "scope",
    title: "Scope of this policy",
    content: (
      <>
        <p>
          This sample policy applies to appointments for beauty and wellness
          services booked with Golden Touch Beauty Centre. Product-order
          cancellations and returns are handled separately under the Delivery
          and Returns Policy.
        </p>
        <p>
          The final version must state its effective date and apply consistently
          across online, telephone, WhatsApp, walk-in, staff-created, and other
          approved booking channels.
        </p>
      </>
    ),
  },
  {
    id: "requesting-change",
    title: "Requesting cancellation or rescheduling",
    content: (
      <>
        <p>
          Customers should request cancellation or rescheduling as early as
          possible through the account dashboard where available or through an
          approved Makola or Tse Addo contact channel.
        </p>
        <p>
          A request is not complete until Golden Touch records or acknowledges
          it. Customers should retain the booking reference and any
          cancellation or rescheduling confirmation.
        </p>
      </>
    ),
  },
  {
    id: "notice-period",
    title: "Required notice period",
    content: (
      <>
        <p>
          The minimum notice period for cancellation or rescheduling has not
          yet been approved. The final policy must state the exact number of
          hours or days required and explain how notice is calculated for
          weekends, public holidays, group bookings, bridal services, and
          appointments requiring advance preparation.
        </p>
        <p>
          Until the final rule is approved, management should review requests
          consistently and communicate any proposed fee or deduction before
          accepting payment where reasonably possible.
        </p>
      </>
    ),
  },
  {
    id: "rescheduling",
    title: "Rescheduling",
    content: (
      <>
        <p>
          Rescheduling is subject to staff, service, branch, date, and time
          availability. Golden Touch may offer another time or an alternative
          branch where the original preference cannot be met.
        </p>
        <p>
          A changed appointment becomes confirmed only after any required
          customer acceptance, price adjustment, or payment step is completed.
          Repeated rescheduling limits and any related fee require approval in
          the final policy.
        </p>
      </>
    ),
  },
  {
    id: "late-arrival",
    title: "Late arrival",
    content: (
      <p>
        Late arrival may shorten the available service time, require a
        different service, or result in rescheduling or cancellation where
        there is not enough time to proceed safely and without delaying later
        appointments. The final policy must specify the approved grace period,
        any fee treatment, and whether full service charges may apply.
      </p>
    ),
  },
  {
    id: "no-show",
    title: "Missed appointments and no-shows",
    content: (
      <p>
        A customer who does not attend and has not completed an acknowledged
        cancellation may be marked as a no-show. The final business and legal
        review must decide whether the payment is forfeited, partly refundable,
        transferable once, or handled another way. Any no-show consequence must
        be displayed before payment and applied consistently.
      </p>
    ),
  },
  {
    id: "customer-refunds",
    title: "Customer cancellation refunds",
    content: (
      <>
        <p>
          Refund eligibility may depend on the approved notice period, service
          type, preparation already performed, third-party costs, special-event
          arrangements, and whether the appointment has begun. Final deduction
          amounts and non-refundable charges have not yet been approved.
        </p>
        <p>
          Golden Touch should explain the decision and maintain a record linking
          an approved refund, partial refund, credit, or rejection to the
          original booking and payment.
        </p>
      </>
    ),
  },
  {
    id: "consultation-fee",
    title: "Separate consultation fee",
    content: (
      <>
        <p>
          Where Golden Touch offers the separate consultation described in the
          PRD, the consultation fee is GHS 200 and is non-refundable. This rule
          must be displayed clearly before the customer pays.
        </p>
        <p>
          This provision applies only when that separate consultation service
          is active and selected. It does not automatically convert every
          discussion or ordinary service consultation into a GHS 200 charge.
        </p>
      </>
    ),
  },
  {
    id: "golden-touch-cancellation",
    title: "Cancellation by Golden Touch",
    content: (
      <>
        <p>
          If Golden Touch cannot provide a confirmed service, management may
          propose another date, time, suitable provider, or branch. The
          customer should be informed using the available account and contact
          details.
        </p>
        <p>
          Where the customer does not accept a reasonable replacement, Golden
          Touch should provide an appropriate refund for the unprovided service,
          subject to the final policy and applicable law.
        </p>
      </>
    ),
  },
  {
    id: "completed-services",
    title: "Completed services and complaints",
    content: (
      <>
        <p>
          Completed services are not normally refundable only because a result
          differs from a subjective preference or reference image. However,
          complaints about service quality, injury, adverse reaction, incorrect
          service, misrepresentation, or failure to provide an agreed service
          should be reviewed promptly and fairly.
        </p>
        <p>
          Customers should contact Golden Touch as soon as possible, provide the
          booking reference and relevant information, and seek urgent medical
          care where symptoms require it. This policy does not limit rights or
          remedies that cannot lawfully be excluded.
        </p>
      </>
    ),
  },
  {
    id: "payment-errors",
    title: "Duplicate, failed, or reversed payments",
    content: (
      <p>
        Suspected duplicate charges, failed transactions, reversals, or payments
        made without a completed booking should be investigated using the
        provider reference and Golden Touch records. A browser success message
        alone is not final payment proof. Approved corrections should be linked
        to the original transaction and processed only once.
      </p>
    ),
  },
  {
    id: "refund-method-timing",
    title: "Refund method and processing time",
    content: (
      <>
        <p>
          Approved refunds should normally return through the original payment
          method where possible. Payment-provider, bank, Mobile Money, card, and
          settlement timelines may affect when funds become visible.
        </p>
        <p>
          Golden Touch’s internal review period and expected external processing
          ranges must be inserted after Korapay and other payment capabilities
          are verified. Customers should receive a refund reference or written
          status where available.
        </p>
      </>
    ),
  },
  {
    id: "contact-review",
    title: "Contact and policy review",
    content: (
      <p>
        Cancellation, rescheduling, and refund questions may be directed to the
        selected branch using the Contact page. The final policy must add an
        escalation process, responsible contact, complaint timeline, effective
        date, approved notice period, grace period, deductions, and refund
        processing targets following business and legal review.
      </p>
    ),
  },
];

export default function CancellationRefundsPage() {
  return (
    <PolicyLayout
      eyebrow="Golden Touch policies"
      title="Booking Cancellation and Refund Policy"
      description="Provisional rules for appointment changes, late arrival, no-shows, customer cancellations, Golden Touch cancellations, and service-payment refunds."
      status="This sample is for development and testing only. Notice periods, grace periods, deductions, no-show treatment, refund timelines, and escalation procedures require business and legal approval before launch."
      sections={sections}
    />
  );
}
