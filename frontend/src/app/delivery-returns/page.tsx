import type { Metadata } from "next";

import {
  PolicyLayout,
  type PolicySection,
} from "@/components/legal/policy-layout";

export const metadata: Metadata = {
  title: "Product Delivery and Returns Policy",
  description:
    "Development-draft policy covering Golden Touch product delivery, clinic pickup, return requests, hygiene restrictions, refunds, and preorders.",
};

const sections: PolicySection[] = [
  {
    id: "scope",
    title: "Scope of this policy",
    content: (
      <>
        <p>
          This sample policy applies to physical products purchased from Golden
          Touch Beauty Centre through the website or another approved sales
          channel. Appointment cancellation and service-payment refunds are
          covered by the separate Booking Cancellation and Refund Policy.
        </p>
        <p>
          Final delivery areas, carriers, charges, service levels, and legal
          entity information must be approved before this policy is used in
          production.
        </p>
      </>
    ),
  },
  {
    id: "order-acceptance",
    title: "Order acceptance and stock",
    content: (
      <>
        <p>
          An order remains subject to product price, variant, quantity, stock,
          payment, and fulfilment verification. Items shown in a cart are not
          guaranteed until the required reservation and payment steps are
          successfully completed.
        </p>
        <p>
          If Golden Touch cannot fulfil an item because of a stock, pricing, or
          catalogue error, management may offer an available alternative or
          cancel and appropriately refund the affected item or order.
        </p>
      </>
    ),
  },
  {
    id: "payment-quotation",
    title: "Payment and delivery quotation",
    content: (
      <>
        <p>
          Cash on delivery is not available. Products and any accepted delivery
          charge must be paid in full before dispatch.
        </p>
        <p>
          During the initial delivery workflow, Golden Touch may prepare a
          manual quotation based on the destination, order, parcel, carrier,
          and available service. The customer must accept and pay the quoted
          amount before delivery is arranged. Final quotation validity and
          repricing rules require approval.
        </p>
      </>
    ),
  },
  {
    id: "address-contact",
    title: "Delivery address and contact details",
    content: (
      <>
        <p>
          Customers must provide a complete and accurate recipient name,
          delivery address, telephone number, and any reasonable access
          instructions. Golden Touch is not responsible for avoidable delay
          caused by incomplete or incorrect information supplied by the
          customer.
        </p>
        <p>
          Address changes requested after payment or dispatch may require
          approval, a revised quotation, or cancellation where the carrier
          cannot redirect the parcel safely.
        </p>
      </>
    ),
  },
  {
    id: "delivery-estimates",
    title: "Dispatch and delivery estimates",
    content: (
      <>
        <p>
          Delivery estimates begin after payment and fulfilment approval and are
          not guaranteed arrival dates. Carriers, traffic, weather, customs,
          public holidays, security events, incomplete information, or other
          circumstances outside reasonable control may cause delay.
        </p>
        <p>
          Approved carriers and expected service ranges must be inserted in the
          final policy. Customers should receive available dispatch or tracking
          information when the delivery workflow supports it.
        </p>
      </>
    ),
  },
  {
    id: "failed-delivery",
    title: "Failed delivery and redelivery",
    content: (
      <p>
        If delivery cannot be completed because the recipient is unavailable,
        unreachable, refuses the parcel without an approved return reason, or
        provides an inaccessible or incorrect address, additional storage,
        return, or redelivery charges may apply. Responsibility and charge
        amounts must be approved and disclosed in the final policy.
      </p>
    ),
  },
  {
    id: "clinic-pickup",
    title: "Clinic pickup",
    content: (
      <>
        <p>
          Checkout should offer only branches with enough eligible stock for
          every requested item and quantity. Customers should wait for a
          “ready for pickup” confirmation before travelling to Makola or Tse
          Addo.
        </p>
        <p>
          The person collecting may be asked for the order reference,
          confirmation message, and reasonable identity or authorization
          evidence. Pickup holding periods and uncollected-order treatment must
          be finalized before launch.
        </p>
      </>
    ),
  },
  {
    id: "inspection",
    title: "Checking products on receipt",
    content: (
      <p>
        Customers should inspect the parcel promptly and report missing,
        incorrect, damaged, leaking, opened, or defective items as soon as
        reasonably possible. Keep the product, packaging, order reference, and
        any requested photographs while the report is reviewed. Do not use a
        product that appears unsafe, tampered with, or materially damaged.
      </p>
    ),
  },
  {
    id: "return-window",
    title: "Fourteen-day return request window",
    content: (
      <>
        <p>
          Return requests must be submitted within 14 days after confirmed
          delivery or clinic pickup. Submitting a request does not automatically
          approve the return.
        </p>
        <p>
          The request should include the order reference, affected product and
          quantity, reason, condition, and any photographs or information
          reasonably required for review.
        </p>
      </>
    ),
  },
  {
    id: "return-condition",
    title: "Product condition",
    content: (
      <>
        <p>
          Unless the product is incorrect, damaged, defective, unsafe, or
          otherwise approved by management, it should be unused, unopened,
          unaltered, and in its original condition and packaging with included
          seals, accessories, and labels.
        </p>
        <p>
          Golden Touch may reject a discretionary return where the item shows
          use, contamination, alteration, avoidable damage, or missing
          packaging that prevents safe resale.
        </p>
      </>
    ),
  },
  {
    id: "hygiene-products",
    title: "Hygiene-sensitive and personal-use products",
    content: (
      <p>
        Opened skincare, makeup, cosmetics, soaps, wigs, hair pieces,
        applicators, and other hygiene-sensitive or personal-use beauty
        products are not normally returnable for change of mind. This
        restriction does not remove rights relating to products that are
        incorrect, defective, damaged, unsafe, misdescribed, or otherwise
        protected by applicable law.
      </p>
    ),
  },
  {
    id: "review-outcome",
    title: "Return review and outcome",
    content: (
      <>
        <p>
          Every return requires management review. Golden Touch may request
          inspection before approving a refund, replacement, exchange, repair,
          store credit, or another appropriate outcome.
        </p>
        <p>
          The decision and reason should be linked to the original order. The
          final policy must define review timelines, escalation, exchange
          availability, and how disagreements are handled.
        </p>
      </>
    ),
  },
  {
    id: "return-delivery",
    title: "Returning the product",
    content: (
      <p>
        Customers should not send a return until Golden Touch provides approval
        and return instructions. The responsible branch, approved carrier,
        delivery method, risk during return, and responsibility for return
        charges must be confirmed in the final operating policy. Unapproved
        parcels may be delayed or refused where they cannot be identified or
        handled safely.
      </p>
    ),
  },
  {
    id: "refunds-charges",
    title: "Refunds and delivery charges",
    content: (
      <>
        <p>
          Approved refunds should normally use the original payment method
          where possible and should be linked to the original order and payment
          reference. Provider and banking timelines may affect when funds
          become visible.
        </p>
        <p>
          Whether original delivery charges, quotation fees, or return-delivery
          charges are refundable depends on the reason for return and the final
          approved policy. Refund processing targets must be added after payment
          provider capabilities are verified.
        </p>
      </>
    ),
  },
  {
    id: "preorders",
    title: "Preorders",
    content: (
      <>
        <p>
          Preorders require full payment. Any displayed availability date is an
          estimate and may change because of suppliers, shipping, customs, or
          circumstances outside reasonable control.
        </p>
        <p>
          Customers should be informed of material date changes and notified
          when stock is ready for pickup or dispatch. Final cancellation and
          refund treatment for delayed preorders requires business and legal
          approval.
        </p>
      </>
    ),
  },
  {
    id: "rights-contact",
    title: "Customer rights and contact",
    content: (
      <>
        <p>
          Nothing in this sample policy is intended to remove consumer rights
          or remedies that cannot lawfully be excluded. Complaints should be
          reviewed fairly using the order, payment, stock, delivery, and
          communication records.
        </p>
        <p>
          Delivery, pickup, and return questions may be directed to Golden Touch
          through the branch contacts shown on the Contact page. The final
          policy must provide an official escalation contact and effective
          date.
        </p>
      </>
    ),
  },
];

export default function DeliveryReturnsPage() {
  return (
    <PolicyLayout
      eyebrow="Golden Touch policies"
      title="Product Delivery and Returns Policy"
      description="Provisional rules for paid delivery quotations, clinic pickup, product inspection, return requests, hygiene-sensitive goods, refunds, and preorders."
      status="This sample is for development and testing only. Delivery areas, carriers, charges, timelines, pickup holding periods, return shipping, refund targets, and escalation procedures require business and legal approval before launch."
      sections={sections}
    />
  );
}
