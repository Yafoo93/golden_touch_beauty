import type { Metadata } from "next";
import Image from "next/image";
import { notFound } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { ServiceCard } from "@/components/catalogue/service-card";
import { WhatsAppPriceEnquiry } from "@/components/catalogue/whatsapp-price-enquiry";
import {
  formatBranchTime,
  formatOpeningDays,
} from "@/lib/branch-formatters";
import { formatGhanaCedis } from "@/lib/formatters";
import {
  getRelatedServices,
  getServiceDetail,
  type ServiceDetail,
} from "@/lib/services";

function durationLabel(minutes: number) {
  if (minutes < 60) return `${minutes} minutes`;
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  return remaining
    ? `${hours} hr ${remaining} min`
    : `${hours} ${hours === 1 ? "hour" : "hours"}`;
}

function priceLabel(service: ServiceDetail) {
  if (service.price_type === "quotation") return "Contact us for a quotation";
  if (service.price_type === "range" && service.maximum_price) {
    return `${formatGhanaCedis(service.price)} – ${formatGhanaCedis(service.maximum_price)}`;
  }
  if (service.price_type === "starting_from") {
    return `From ${formatGhanaCedis(service.price)}`;
  }
  if (service.price_type === "options") {
    return `Options from ${formatGhanaCedis(service.price)}`;
  }
  return formatGhanaCedis(service.price);
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const service = await getServiceDetail(slug);
  if (!service) return { title: "Service Not Found" };
  return {
    title: service.name,
    description: service.short_description,
  };
}

export default async function ServiceDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const service = await getServiceDetail(slug);
  if (!service) notFound();
  const relatedServices = await getRelatedServices(service);

  return (
    <main className="service-detail-page">
      <section className="service-detail-hero">
        <div className="service-detail-hero__image">
          <Image
            src={service.image_path || "/images/hero1.jpeg"}
            alt={`${service.name} service`}
            fill
            priority
            sizes="(max-width: 52rem) 100vw, 50vw"
          />
        </div>
        <div className="service-detail-hero__content">
          <p>{service.category}</p>
          <h1>{service.name}</h1>
          <span>{service.short_description}</span>
          <dl className="service-detail-facts">
            <div>
              <dt>Price</dt>
              <dd>{priceLabel(service)}</dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{durationLabel(service.duration_minutes)}</dd>
            </div>
            <div>
              <dt>Service setting</dt>
              <dd>
                {[
                  service.is_clinic_service ? "At the clinic" : "",
                  service.is_home_service ? "Home service" : "",
                ]
                  .filter(Boolean)
                  .join(" or ")}
              </dd>
            </div>
          </dl>
          {service.pricing_notes ? (
            <p className="service-detail-hero__pricing-note">
              {service.pricing_notes}
            </p>
          ) : null}
          <div className="service-detail-hero__actions">
            {service.price_type === "quotation" ? <WhatsAppPriceEnquiry itemType="service" itemName={service.name} branches={service.available_branches.map((branch) => ({ code: branch.code, name: branch.name, whatsapp_number: branch.whatsapp_number || branch.secondary_whatsapp_number || branch.telephone_number }))} /> : <ButtonLink
              href={`/book?service=${encodeURIComponent(service.slug)}`}
              size="large"
            >
              Book this service
            </ButtonLink>}
            <ButtonLink href="/services" variant="outline" size="large">
              Back to services
            </ButtonLink>
          </div>
        </div>
      </section>

      {service.before_image_url && service.after_image_url ? (
        <section className="service-result-pair" aria-labelledby="service-results-title">
          <header><p>Real treatment result</p><h2 id="service-results-title">Before and after</h2><span>Approved client images are shown with explicit publication consent. Individual results vary.</span></header>
          <div>
            <figure><div><img src={service.before_image_url} alt={`Before ${service.name}`} /></div><figcaption>Before</figcaption></figure>
            <figure><div><img src={service.after_image_url} alt={`After ${service.name}`} /></div><figcaption>After</figcaption></figure>
          </div>
        </section>
      ) : null}

      <section className="service-detail-description" aria-labelledby="service-description-title">
        <div>
          <p>About this service</p>
          <h2 id="service-description-title">What to expect</h2>
        </div>
        <div>
          {service.description
            .split(/\n+/)
            .filter(Boolean)
            .map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          <aside>
            <strong>Payment</strong>
            <span>
              {service.requires_full_payment
                ? "Full payment is required to secure this service."
                : "Payment requirements are confirmed during booking."}
              {service.allows_pay_at_clinic
                ? " Payment may be completed online or at the clinic."
                : " Payment is completed online."}
            </span>
          </aside>
        </div>
      </section>

      {service.price_type === "options" && service.price_options.length ? (
        <section
          className="service-detail-options"
          aria-labelledby="service-options-title"
        >
          <header>
            <p>Choose what suits you</p>
            <h2 id="service-options-title">Service price options</h2>
            <span>
              Select your preferred option when booking. Availability is
              confirmed for your chosen branch and date.
            </span>
          </header>
          <div className="service-detail-options__grid">
            {service.price_options.map((option) => (
              <article key={option.id}>
                <div>
                  <h3>{option.name}</h3>
                  {option.description ? <p>{option.description}</p> : null}
                </div>
                <dl>
                  <div>
                    <dt>Price</dt>
                    <dd>{formatGhanaCedis(option.price)}</dd>
                  </div>
                  {option.duration_minutes ? (
                    <div>
                      <dt>Duration</dt>
                      <dd>{durationLabel(option.duration_minutes)}</dd>
                    </div>
                  ) : null}
                </dl>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="service-detail-branches" aria-labelledby="service-branches-title">
        <header>
          <p>Where it is available</p>
          <h2 id="service-branches-title">Choose your branch</h2>
          <span>
            Branch selection and real availability are confirmed during booking.
          </span>
        </header>
        <div className="service-detail-branches__grid">
          {service.available_branches.map((branch) => (
            <article key={branch.id}>
              <h3>{branch.name}</h3>
              <p>{branch.address}</p>
              <dl>
                <div>
                  <dt>Opening days</dt>
                  <dd>{formatOpeningDays(branch.opening_days)}</dd>
                </div>
                <div>
                  <dt>Hours</dt>
                  <dd>
                    {formatBranchTime(branch.opening_time)} –{" "}
                    {formatBranchTime(branch.closing_time)}
                  </dd>
                </div>
              </dl>
              {service.price_type === "quotation" ? <WhatsAppPriceEnquiry compact itemType="service" itemName={service.name} branches={[{ code: branch.code, name: branch.name, whatsapp_number: branch.whatsapp_number || branch.secondary_whatsapp_number || branch.telephone_number }]} /> : <ButtonLink
                href={`/book?service=${encodeURIComponent(service.slug)}&branch=${encodeURIComponent(branch.code)}`}
                size="small"
              >
                Book at {branch.name}
              </ButtonLink>}
            </article>
          ))}
        </div>
      </section>

      {relatedServices.length ? (
        <section className="related-catalogue" aria-labelledby="related-services-title">
          <header className="related-catalogue__heading">
            <p>Continue exploring</p>
            <h2 id="related-services-title">Related services</h2>
            <span>Other treatments in {service.category}.</span>
          </header>
          <div className="catalogue-grid">
            {relatedServices.map((relatedService) => (
              <ServiceCard key={relatedService.slug} {...relatedService} />
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}
