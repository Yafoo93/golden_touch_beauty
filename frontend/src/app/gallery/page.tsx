import type { Metadata } from "next";
import Image from "next/image";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import { getGalleryItems } from "@/lib/gallery";

export const metadata: Metadata = {
  title: "Beauty Gallery",
  description:
    "Explore selected skin, hair, bridal, makeup, and traditional styling imagery from Golden Touch Beauty Centre.",
};

export default async function GalleryPage() {
  const galleryItems = await getGalleryItems();
  return (
    <main className="gallery-page">
      <PageHero
        eyebrow="Golden Touch gallery"
        title="Beauty in"
        accentTitle="Every Detail"
        description="Explore selected imagery across our skin, hair, bridal, makeup, and traditional styling services."
        backgroundImage="/images/bridal.jpeg"
        backgroundPosition="center 35%"
        size="compact"
      />

      <section className="gallery-page__content" aria-labelledby="gallery-title">
        <div className="gallery-page__heading">
          <p>Our work and services</p>
          <h2 id="gallery-title">The Golden Touch experience</h2>
          <span>
            Service results vary by client. Your consultation helps us
            recommend an appropriate treatment or styling approach.
          </span>
        </div>

        {galleryItems.length ? <div className="gallery-grid">
          {galleryItems.map((item) => (
            <figure
              className={`gallery-card gallery-card--${item.display_size}`}
              key={item.id}
            >
              <Image
                src={item.image_url}
                alt={item.alt_text}
                fill
                sizes={
                  item.display_size === "wide"
                    ? "(max-width: 720px) 100vw, 66vw"
                    : "(max-width: 720px) 100vw, 33vw"
                }
              />
              <figcaption>
                <span>{item.category}</span>
                <h3>{item.title}</h3>
              </figcaption>
            </figure>
          ))}
        </div> : (
          <EmptyState title="Gallery updates are coming" description="Approved Golden Touch work will appear here soon." />
        )}
      </section>

      <section className="gallery-cta" aria-labelledby="gallery-cta-title">
        <div>
          <p>Plan your visit</p>
          <h2 id="gallery-cta-title">Ready for your Golden Touch?</h2>
          <span>
            Choose a service and the branch that is most convenient for you.
          </span>
        </div>
        <div className="gallery-cta__actions">
          <ButtonLink href="/services" variant="outline">
            Browse services
          </ButtonLink>
          <ButtonLink href="/book">Book an appointment</ButtonLink>
        </div>
      </section>
    </main>
  );
}
