import Image from "next/image";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { formatGhanaCedis } from "@/lib/formatters";

export type ProductCardProps = {
  name: string;
  slug: string;
  category: string;
  description: string;
  price: number | string;
  imageSrc: string;
  variantLabel?: string;
  inStock: boolean;
  badge?: string;
};

export function ProductCard({
  name,
  slug,
  category,
  description,
  price,
  imageSrc,
  variantLabel,
  inStock,
  badge,
}: ProductCardProps) {
  const detailsHref = `/shop/${slug}`;

  return (
    <article className="catalogue-card product-card">
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
        <div className="product-card__meta">
          {variantLabel ? <span>{variantLabel}</span> : null}
          <span
            className={
              inStock ? "stock stock--available" : "stock stock--unavailable"
            }
          >
            {inStock ? "In stock" : "Out of stock"}
          </span>
        </div>
        <div className="catalogue-card__footer">
          <p className="catalogue-card__price">{formatGhanaCedis(price)}</p>
          <ButtonLink
            href={detailsHref}
            variant={inStock ? "gold" : "black"}
            size="small"
            aria-label={`View ${name}`}
          >
            View product
          </ButtonLink>
        </div>
      </div>
    </article>
  );
}
