import Image from "next/image";

import { ButtonLink } from "@/components/ui/button";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ManagementProduct } from "@/lib/management-products";

function priceLabel(product: ManagementProduct) {
  if (!product.minimum_price) return "No active price";
  if (
    product.maximum_price &&
    product.maximum_price !== product.minimum_price
  ) {
    return `${formatGhanaCedis(product.minimum_price)} – ${formatGhanaCedis(product.maximum_price)}`;
  }
  return formatGhanaCedis(product.minimum_price);
}

export function ManagementProductList({
  products,
}: {
  products: ManagementProduct[];
}) {
  return (
    <div className="management-service-list management-product-list">
      {products.map((product) => (
        <article className="management-service-card" key={product.id}>
          <div className="management-service-card__image">
            <Image
              src={product.image_path || "/images/hero2.jpeg"}
              alt=""
              fill
              sizes="12rem"
            />
          </div>
          <div className="management-service-card__content">
            <header>
              <div>
                <p>{product.category}</p>
                <h2>{product.name}</h2>
                <span>
                  {product.brand ? `${product.brand} · ` : ""}/{product.slug}
                </span>
              </div>
              <div className="management-service-card__statuses">
                <span
                  className={`status-badge status-badge--${product.publication_state === "published" ? "active" : "inactive"}`}
                >
                  {product.publication_state[0].toUpperCase() +
                    product.publication_state.slice(1)}
                </span>
                {product.low_stock_count ? (
                  <span className="status-badge management-product-card__low-stock">
                    {product.low_stock_count} low stock
                  </span>
                ) : null}
                {product.is_featured ? (
                  <span className="status-badge management-service-card__featured">
                    Featured
                  </span>
                ) : null}
              </div>
            </header>

            <dl className="management-service-card__facts management-product-card__facts">
              <div><dt>Price</dt><dd>{priceLabel(product)}</dd></div>
              <div><dt>Variants</dt><dd>{product.active_variant_count} active · {product.variant_count} total</dd></div>
              <div><dt>Available</dt><dd>{product.total_available}</dd></div>
              <div><dt>Reserved</dt><dd>{product.total_reserved}</dd></div>
              <div><dt>On hand</dt><dd>{product.total_on_hand}</dd></div>
            </dl>

            <div className="management-service-card__branches">
              <strong>Stock by branch</strong>
              {product.branch_stock.length ? (
                <div>
                  {product.branch_stock.map((stock) => (
                    <span
                      className={
                        stock.branch_is_active
                          ? "management-service-card__branch management-service-card__branch--available"
                          : "management-service-card__branch"
                      }
                      key={stock.branch_id}
                    >
                      {stock.branch_name}: {stock.quantity_available} available ·{" "}
                      {stock.quantity_reserved} reserved · {stock.quantity_on_hand} on hand
                      {!stock.branch_is_active ? " · branch inactive" : ""}
                    </span>
                  ))}
                </div>
              ) : (
                <span>No branch inventory records</span>
              )}
            </div>

            <p className="content-editor__audit">
              Last updated{" "}
              {new Intl.DateTimeFormat("en-GH", {
                dateStyle: "medium",
                timeStyle: "short",
              }).format(new Date(product.updated_at))}
            </p>
            <div className="management-service-card__actions">
              <ButtonLink
                href={`/management/products/${product.id}`}
                size="small"
              >
                Edit product
              </ButtonLink>
              {product.is_active && product.is_published ? (
                <ButtonLink
                  href={`/shop/${product.slug}`}
                  variant="outline"
                  size="small"
                >
                  View public product
                </ButtonLink>
              ) : null}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}
