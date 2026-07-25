import Image from "next/image";

import { ButtonLink } from "@/components/ui/button";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ManagementService } from "@/lib/management-services";

function priceLabel(service: ManagementService) {
  if (service.price_type === "quotation") return "Quotation";
  if (service.price_type === "range" && service.maximum_price) {
    return `${formatGhanaCedis(service.price)} – ${formatGhanaCedis(service.maximum_price)}`;
  }
  if (service.price_type === "starting_from") {
    return `From ${formatGhanaCedis(service.price)}`;
  }
  return formatGhanaCedis(service.price);
}

export function ManagementServiceList({
  services,
}: {
  services: ManagementService[];
}) {
  return (
    <div className="management-service-list">
      {services.map((service) => {
        const publicBranches = service.branch_availability.filter(
          (availability) =>
            availability.is_available && availability.branch_is_active,
        );
        return (
          <article className="management-service-card" key={service.id}>
            <div className="management-service-card__image">
              <Image
                src={service.image_path || "/images/hero1.jpeg"}
                alt=""
                fill
                sizes="12rem"
              />
            </div>
            <div className="management-service-card__content">
              <header>
                <div>
                  <p>{service.category}</p>
                  <h2>{service.name}</h2>
                  <span>/{service.slug}</span>
                </div>
                <div className="management-service-card__statuses">
                  <span className={`status-badge status-badge--${service.publication_state === "published" ? "active" : "inactive"}`}>
                    {service.publication_state[0].toUpperCase() + service.publication_state.slice(1)}
                  </span>
                  {service.is_featured ? (
                    <span className="status-badge management-service-card__featured">Featured</span>
                  ) : null}
                </div>
              </header>
              <dl className="management-service-card__facts">
                <div><dt>Price</dt><dd>{priceLabel(service)}</dd></div>
                <div><dt>Duration</dt><dd>{service.duration_minutes} minutes</dd></div>
                <div><dt>Payment</dt><dd>{service.requires_full_payment ? "Full payment" : "Configured during booking"}{service.allows_pay_at_clinic ? " · Clinic allowed" : " · Online only"}</dd></div>
                <div><dt>Public branches</dt><dd>{publicBranches.length}</dd></div>
              </dl>
              {service.pricing_notes ? (
                <p className="management-service-card__note">{service.pricing_notes}</p>
              ) : null}
              <div className="management-service-card__branches">
                <strong>Branch assignments</strong>
                {service.branch_availability.length ? (
                  <div>
                    {service.branch_availability.map((availability) => (
                      <span
                        className={
                          availability.is_available && availability.branch_is_active
                            ? "management-service-card__branch management-service-card__branch--available"
                            : "management-service-card__branch"
                        }
                        key={availability.branch_id}
                      >
                        {availability.branch_name}
                        {!availability.branch_is_active
                          ? " · branch inactive"
                          : availability.is_available
                            ? " · available"
                            : " · unavailable"}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span>No branches assigned</span>
                )}
              </div>
              <p className="content-editor__audit">
                Last updated{" "}
                {new Intl.DateTimeFormat("en-GH", {
                  dateStyle: "medium",
                  timeStyle: "short",
                }).format(new Date(service.updated_at))}
              </p>
              <div className="management-service-card__actions">
                <ButtonLink href={`/management/services/${service.id}`} variant="outline" size="small">
                  View and edit
                </ButtonLink>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
