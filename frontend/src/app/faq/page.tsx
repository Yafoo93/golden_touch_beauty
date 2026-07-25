import type { Metadata } from "next";

import { ButtonLink } from "@/components/ui/button";
import { PageHero } from "@/components/ui/page-hero";

export const metadata: Metadata = {
  title: "Frequently Asked Questions",
  description:
    "Answers to common questions about Golden Touch services, bookings, payments, products, branches, and appointment preparation.",
};

const faqGroups = [
  {
    title: "Appointments and branches",
    questions: [
      {
        question: "Where are Golden Touch Beauty Centre branches located?",
        answer:
          "Golden Touch currently operates at Makola and Tse Addo in Accra. The Contact page contains each active branch’s address, telephone and WhatsApp numbers, opening hours, and available map link.",
      },
      {
        question: "How do I book an appointment?",
        answer:
          "Select Book Now, choose a branch, select an available service, and continue through the date, contact-detail, and payment steps. Availability is based on the selected branch.",
      },
      {
        question: "Can I choose which branch provides my service?",
        answer:
          "Yes. Branch selection is part of the booking process. A service will only appear when it is active and available at the branch you selected.",
      },
      {
        question: "How long should I allow for an appointment?",
        answer:
          "Many services are expected to take approximately one to two hours, but the exact duration depends on the selected service and your individual requirements. Review the displayed duration and confirm any special timing needs with the branch.",
      },
    ],
  },
  {
    title: "Services and preparation",
    questions: [
      {
        question: "Which beauty services are available?",
        answer:
          "Golden Touch offers skin and clinical-aesthetic services, hair care and styling, bridal makeup and gele styling, full-body treatments, and face and body products. Current availability may differ by branch.",
      },
      {
        question: "What information should I share before a skin treatment?",
        answer:
          "Tell the team about allergies, current irritation, pregnancy, medication, medical conditions, recent procedures, previous reactions, and products you use. This information helps the team decide whether a service should proceed, change, or be postponed.",
      },
      {
        question: "Should I stop using skincare products before my appointment?",
        answer:
          "Do not make major routine changes without appropriate guidance. If you use strong exfoliating, prescription, or irritation-causing products, contact the branch before your appointment and explain what you use.",
      },
      {
        question: "How should I prepare for bridal services?",
        answer:
          "Begin with a consultation so the team can understand your date, location, preferred look, hair or gele requirements, timing, and any additional participants. Final inclusions and pricing should be agreed before confirmation.",
      },
    ],
  },
  {
    title: "Payments, products, and policies",
    questions: [
      {
        question: "Do services require full payment?",
        answer:
          "Yes. Services require full payment. Depending on the booking option made available, payment may be completed online or at the clinic. The applicable method and amount should be shown before confirmation.",
      },
      {
        question: "Can I buy products online and choose a pickup branch?",
        answer:
          "The shop and checkout are designed to support branch pickup. Eligible pickup branches are calculated from current stock for the products and quantities in your cart.",
      },
      {
        question: "What happens if a product is unavailable at my preferred branch?",
        answer:
          "The checkout should show whether a branch can fulfil every cart item. You may need to choose another eligible branch, adjust the cart, or contact Golden Touch for assistance.",
      },
      {
        question: "Where can I read the cancellation, refund, delivery, and return rules?",
        answer:
          "Dedicated policy pages are being prepared. The applicable terms should be reviewed before payment or confirmation. Contact a branch if you need help with an existing booking or order while those final policies are being approved.",
      },
    ],
  },
] as const;

export default function FaqPage() {
  return (
    <main className="faq-page">
      <PageHero
        eyebrow="Helpful information"
        title="Frequently Asked"
        accentTitle="Questions"
        description="Find quick answers about appointments, branches, services, payments, products, and preparing for your visit."
        backgroundImage="/images/hero2.jpeg"
        backgroundPosition="center 46%"
        size="compact"
      />

      <section className="faq-page__content" aria-labelledby="faq-title">
        <div className="faq-page__heading">
          <p>How can we help?</p>
          <h2 id="faq-title">Answers before your Golden Touch visit</h2>
          <span>
            These draft answers reflect the current system and provisional
            business rules. Final policy wording will replace relevant answers
            when approved.
          </span>
        </div>

        <div className="faq-groups">
          {faqGroups.map((group) => (
            <section className="faq-group" key={group.title}>
              <h3>{group.title}</h3>
              <div className="faq-list">
                {group.questions.map((item) => (
                  <details className="faq-item" key={item.question}>
                    <summary>
                      <span>{item.question}</span>
                      <span className="faq-item__icon" aria-hidden="true">
                        +
                      </span>
                    </summary>
                    <div className="faq-item__answer">
                      <p>{item.answer}</p>
                    </div>
                  </details>
                ))}
              </div>
            </section>
          ))}
        </div>
      </section>

      <section className="faq-cta" aria-labelledby="faq-cta-title">
        <div>
          <p>Still need help?</p>
          <h2 id="faq-cta-title">Speak with a Golden Touch branch</h2>
          <span>
            Contact Makola or Tse Addo for guidance about a service, booking,
            product, or existing order.
          </span>
        </div>
        <div className="faq-cta__actions">
          <ButtonLink href="/contact" variant="outline">
            Contact a branch
          </ButtonLink>
          <ButtonLink href="/book">Book an appointment</ButtonLink>
        </div>
      </section>
    </main>
  );
}
