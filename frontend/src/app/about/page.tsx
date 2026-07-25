import type { Metadata } from "next";
import Image from "next/image";

import { ButtonLink } from "@/components/ui/button";
import { PageHero } from "@/components/ui/page-hero";
import { getWebsiteContent } from "@/lib/website-content";

export const metadata: Metadata = {
  title: "About Us",
  description:
    "Learn about Golden Touch Beauty Centre, our approach to personal care, and the values behind our Makola and Tse Addo branches.",
};

const values = [
  {
    number: "01",
    title: "Care with purpose",
    description:
      "We listen first, then shape each service around the client’s needs, comfort, and personal beauty goals.",
  },
  {
    number: "02",
    title: "Professional standards",
    description:
      "We value careful consultation, responsible treatment practices, clean environments, and consistent service delivery.",
  },
  {
    number: "03",
    title: "Honest guidance",
    description:
      "We communicate clearly about treatments, products, expectations, and aftercare so clients can make informed choices.",
  },
  {
    number: "04",
    title: "Beauty for every journey",
    description:
      "From everyday personal care to bridal preparation and specialist treatments, every client deserves to feel welcome.",
  },
];

const contentDefaults = {
  "about-hero-description":
    "Golden Touch Beauty Centre brings professional skin, hair, body, bridal, and personal-care services together across our Makola and Tse Addo branches.",
  "about-story-title": "Personal care, delivered with intention",
  "about-story-paragraph-1":
    "Golden Touch was created to give clients a trusted place for beauty, wellness, and personal care. Our work brings together clinical aesthetics, hair and bridal styling, full-body treatments, and carefully selected face and body products.",
  "about-story-paragraph-2":
    "We believe a good beauty experience is more than the final result. It should begin with listening, continue with respectful and professional care, and leave every client feeling confident about the service they received.",
};

export default async function AboutPage() {
  const content = await getWebsiteContent(contentDefaults);
  return (
    <main className="about-page">
      <PageHero
        eyebrow="The Golden Touch story"
        title="Beauty Care Built"
        accentTitle="Around You"
        description={content["about-hero-description"]}
        backgroundImage="/images/hero2.jpeg"
        backgroundPosition="center 46%"
        size="compact"
      />

      <section className="about-story" aria-labelledby="about-story-title">
        <div className="about-story__image">
          <Image
            src="/images/facial_treatment.jpeg"
            alt="A professional facial treatment at a beauty centre"
            fill
            sizes="(max-width: 800px) 100vw, 48vw"
          />
        </div>
        <div className="about-story__content">
          <p className="about-section-label">Who we are</p>
          <h2 id="about-story-title">{content["about-story-title"]}</h2>
          <p>{content["about-story-paragraph-1"]}</p>
          <p>{content["about-story-paragraph-2"]}</p>
          <div className="about-story__actions">
            <ButtonLink href="/services">Explore our services</ButtonLink>
            <ButtonLink href="/contact" variant="outline">
              Visit a branch
            </ButtonLink>
          </div>
        </div>
      </section>

      <section className="about-values" aria-labelledby="about-values-title">
        <div className="about-values__heading">
          <p className="about-section-label">What guides us</p>
          <h2 id="about-values-title">Our values</h2>
          <p>
            These principles shape how we welcome clients, recommend care, and
            deliver every Golden Touch experience.
          </p>
        </div>
        <div className="about-values__grid">
          {values.map((value) => (
            <article className="about-value-card" key={value.number}>
              <span aria-hidden="true">{value.number}</span>
              <h3>{value.title}</h3>
              <p>{value.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="about-presence" aria-labelledby="about-presence-title">
        <div>
          <p className="about-section-label">Our presence</p>
          <h2 id="about-presence-title">Two branches, one standard of care</h2>
          <p>
            Clients can find Golden Touch at Makola and Tse Addo. Service and
            product availability can be managed by branch, helping each
            location serve its clients accurately.
          </p>
        </div>
        <div className="about-presence__actions">
          <ButtonLink href="/contact" variant="outline">
            View branch details
          </ButtonLink>
          <ButtonLink href="/book">Book an appointment</ButtonLink>
        </div>
      </section>
    </main>
  );
}
