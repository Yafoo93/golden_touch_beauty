import Image from "next/image";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { formatGhanaCedis } from "@/lib/formatters";

export type ServiceCardProps = {
  name: string;
  slug: string;
  category: string;
  description: string;
  price: number | string;
  durationMinutes: number;
  imageSrc: string;
  availableAt: string[];
  badge?: string;
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
          sizes="(max-width: 48rem) 100vw, (max-width: 75rem) 50vw, 33vw"
          className="catalogue-card__image"
        />
        {badge ? <span className="catalogue-card__badge">{badge}</span> : null}
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
          <p className="catalogue-card__price">{formatGhanaCedis(price)}</p>
          <ButtonLink
            href={`/book?service=${encodeURIComponent(slug)}`}
            size="small"
            aria-label={`Book ${name}`}
          >
            Book service
          </ButtonLink>
        </div>
      </div>
    </article>
  );
}
