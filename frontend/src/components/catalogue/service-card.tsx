import Image from "next/image";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { formatGhanaCedis } from "@/lib/formatters";
import { WhatsAppPriceEnquiry, type EnquiryBranch } from "./whatsapp-price-enquiry";

export type ServiceCardProps = {
  id?: string;
  name: string;
  slug: string;
  category: string;
  description: string;
  price: number | string;
  durationMinutes: number;
  imageSrc: string;
  availableAt: string[];
  badge?: string;
  priceType?: string;
  allowsPayAtClinic?: boolean;
  priceOptions?: {
    id: string;
    name: string;
    price: string;
    duration_minutes: number | null;
  }[];
  hasResultImages?: boolean;
  enquiryBranches?: EnquiryBranch[];
};

export function ServiceCard({
  name,
  slug,
  category,
  description,
  price,
  durationMinutes,
  imageSrc,
  availableAt,
  badge,
  priceType,
  hasResultImages,
  enquiryBranches = [],
}: ServiceCardProps) {
  const detailsHref = `/services/${slug}`;

  return (
    <article className="catalogue-card service-card">
      <Link
        href={detailsHref}
        className="catalogue-card__media"
        aria-label={`View ${name}`}
      >
        <Image
          src={imageSrc}
          alt=""
          fill
          sizes="(max-width: 48rem) 50vw, (max-width: 64rem) 33vw, 25vw"
          className="catalogue-card__image"
        />
          {badge ? <span className="catalogue-card__badge">{badge}</span> : null}
          {hasResultImages ? <span className="catalogue-card__result-badge">Before &amp; after available</span> : null}
      </Link>
      <div className="catalogue-card__body">
        <p className="catalogue-card__category">{category}</p>
        <h3>
          <Link href={detailsHref}>{name}</Link>
        </h3>
        <p className="catalogue-card__description">{description}</p>
        <dl className="catalogue-card__facts">
          <div>
            <dt>Duration</dt>
            <dd>{durationMinutes} minutes</dd>
          </div>
          <div>
            <dt>Available at</dt>
            <dd>{availableAt.join(" and ")}</dd>
          </div>
        </dl>
        <div className="catalogue-card__footer">
          <p className="catalogue-card__price">
            {priceType === "quotation" ? "Contact for price" : priceType === "starting_from" ? `Starting from ${formatGhanaCedis(price)}` : formatGhanaCedis(price)}
          </p>
          {priceType === "quotation" ? <WhatsAppPriceEnquiry compact itemType="service" itemName={name} branches={enquiryBranches} /> : <ButtonLink
            href={detailsHref}
            size="small"
            aria-label={`Book ${name}`}
          >
            View service
          </ButtonLink>}
        </div>
      </div>
    </article>
  );
}
