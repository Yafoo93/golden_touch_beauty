"use client";

import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState, useTransition } from "react";

import { Button, ButtonLink } from "@/components/ui/button";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ServiceCardProps } from "@/components/catalogue/service-card";

export function ServiceSelector({
  services,
  branchCode,
  branchName,
  initialServiceSlugs,
}: {
  services: ServiceCardProps[];
  branchCode: string;
  branchName: string;
  initialServiceSlugs: string[];
}) {
  const availableSlugs = useMemo(
    () => new Set(services.map((service) => service.slug)),
    [services],
  );
  const [selectedSlugs, setSelectedSlugs] = useState(
    () => new Set(initialServiceSlugs.filter((slug) => availableSlugs.has(slug))),
  );
  const [isNavigating, startTransition] = useTransition();
  const router = useRouter();
  const searchParams = useSearchParams();

  function toggleService(slug: string) {
    const next = new Set(selectedSlugs);
    if (next.has(slug)) next.delete(slug);
    else next.add(slug);
    setSelectedSlugs(next);

    const params = new URLSearchParams(searchParams.toString());
    params.delete("service");
    params.set("step", "service");
    params.set("branch", branchCode);
    if (next.size) params.set("services", Array.from(next).join(","));
    else params.delete("services");
    startTransition(() => {
      router.replace(`/book?${params.toString()}`, { scroll: false });
    });
  }

  const selectedServices = services.filter((service) =>
    selectedSlugs.has(service.slug),
  );

  function continueToSchedule() {
    if (!selectedServices.length) return;
    const params = new URLSearchParams();
    params.set("branch", branchCode);
    params.set("services", selectedServices.map((service) => service.slug).join(","));
    params.set("step", "schedule");
    startTransition(() => router.push(`/book?${params.toString()}`));
  }

  return (
    <div className="booking-service-selector">
      <header className="booking-service-selector__header">
        <div>
          <p>Selected branch</p>
          <h2>{branchName}</h2>
          <span>Select every service required for this appointment.</span>
        </div>
        <ButtonLink href={`/book?branch=${encodeURIComponent(branchCode)}`} variant="outline">
          Change branch
        </ButtonLink>
      </header>

      <fieldset>
        <legend>Select one or more services</legend>
        <div className="booking-service-selector__grid">
          {services.map((service) => {
            const selected = selectedSlugs.has(service.slug);
            return (
              <label
                className="booking-service-option"
                data-selected={selected || undefined}
                key={service.slug}
              >
                <input
                  type="checkbox"
                  name="services"
                  value={service.slug}
                  checked={selected}
                  onChange={() => toggleService(service.slug)}
                />
                <span className="booking-service-option__image">
                  <Image
                    src={service.imageSrc || "/images/hero1.jpeg"}
                    alt=""
                    fill
                    sizes="6rem"
                  />
                </span>
                <span className="booking-service-option__content">
                  <small>{service.category}</small>
                  <strong>{service.name}</strong>
                  <span>
                    {service.durationMinutes} minutes · {formatGhanaCedis(service.price)}
                  </span>
                </span>
                <span className="booking-service-option__check" aria-hidden="true">
                  {selected ? "✓" : ""}
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>

      <footer className="booking-service-selector__footer">
        <div aria-live="polite">
          <strong>
            {selectedServices.length}{" "}
            {selectedServices.length === 1 ? "service" : "services"} selected
          </strong>
          <span>
            {selectedServices.length
              ? selectedServices.map((service) => service.name).join(", ")
              : "Choose at least one service to continue."}
          </span>
        </div>
        <Button
          type="button"
          onClick={continueToSchedule}
          disabled={!selectedServices.length || isNavigating}
        >
          {isNavigating ? "Opening schedule..." : "Continue to date and time"}
        </Button>
      </footer>
    </div>
  );
}
