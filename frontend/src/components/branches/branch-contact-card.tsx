import { ButtonLink } from "@/components/ui/button";
import {
  formatBranchTime,
  formatGhanaPhone,
  formatOpeningDays,
  whatsappUrl,
} from "@/lib/branch-formatters";
import type { PublicBranch } from "@/lib/branches";


function ContactIcon({ type }: { type: "location" | "phone" | "clock" | "email" }) {
  const paths = {
    location: <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
    phone: <path d="M6.7 3.8 9 3.2l2.1 5-1.8 1.4a14.6 14.6 0 0 0 5.1 5.1l1.4-1.8 5 2.1-.6 2.3a3 3 0 0 1-3.3 2.3A15.8 15.8 0 0 1 4.4 7.1 3 3 0 0 1 6.7 3.8Z" />,
    clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>,
    email: <><rect x="3.5" y="5.5" width="17" height="13" rx="1.5" /><path d="m4.5 7 7.5 6 7.5-6" /></>,
  };
  return <svg viewBox="0 0 24 24" aria-hidden="true">{paths[type]}</svg>;
}

export function BranchContactCard({ branch }: { branch: PublicBranch }) {
  const telephoneNumbers = [branch.telephone_number, branch.secondary_telephone_number].filter(Boolean);
  const whatsappNumbers = [branch.whatsapp_number, branch.secondary_whatsapp_number].filter(Boolean);

  return (
    <article className="branch-contact-card">
      <header><p>Golden Touch branch</p><h2>{branch.name}</h2></header>
      <dl className="branch-contact-card__details">
        <div><dt><ContactIcon type="location" /><span className="sr-only">Address</span></dt><dd>{branch.address}</dd></div>
        <div><dt><ContactIcon type="clock" /><span className="sr-only">Opening hours</span></dt><dd>{formatOpeningDays(branch.opening_days)}<span>{formatBranchTime(branch.opening_time)} - {formatBranchTime(branch.closing_time)}</span></dd></div>
        <div><dt><ContactIcon type="phone" /><span className="sr-only">Telephone</span></dt><dd>{telephoneNumbers.map((number) => <a href={`tel:${number}`} key={number}>{formatGhanaPhone(number)}</a>)}</dd></div>
        <div>
          <dt><ContactIcon type="email" /><span className="sr-only">Email</span></dt>
          <dd>
            {branch.email ? (
              <a href={`mailto:${branch.email}`}>{branch.email}</a>
            ) : (
              <span>Email address not available yet</span>
            )}
          </dd>
        </div>
      </dl>
      <div className="branch-contact-card__actions">
        {whatsappNumbers.map((number, index) => (
          <ButtonLink
            href={whatsappUrl(number)}
            target="_blank"
            rel="noopener noreferrer"
            variant={index === 0 ? "gold" : "black"}
            size="small"
            aria-label={`Chat with the ${branch.name} branch on WhatsApp at ${formatGhanaPhone(number)}`}
            key={number}
          >
            WhatsApp {formatGhanaPhone(number)}
          </ButtonLink>
        ))}
        {branch.google_maps_url ? (
          <ButtonLink
            href={branch.google_maps_url}
            target="_blank"
            rel="noopener noreferrer"
            variant="outline"
            size="small"
            aria-label={`Open ${branch.name} branch in Google Maps`}
          >
            Open Google Maps
          </ButtonLink>
        ) : (
          <span className="branch-contact-card__unavailable">
            Map location not available yet
          </span>
        )}
      </div>
    </article>
  );
}
