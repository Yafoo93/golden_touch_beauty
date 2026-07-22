import { formatBranchTime, formatGhanaPhone, formatOpeningDays, whatsappUrl } from "@/lib/branch-formatters";
import { ButtonLink } from "@/components/ui/button";
import type { ManagementBranch } from "@/lib/management-branches";

export function ManagementBranchList({ branches }: { branches: ManagementBranch[] }) {
  return (
    <div className="management-branch-list">
      {branches.map((branch) => (
        <article className="management-branch-card" key={branch.id}>
          <header>
            <div>
              <span className="management-branch-card__code">{branch.code}</span>
              <h2>{branch.name}</h2>
            </div>
            <span className={`status-badge status-badge--${branch.is_active ? "active" : "inactive"}`}>
              {branch.is_active ? "Active" : "Inactive"}
            </span>
          </header>

          <p className="management-branch-card__address">{branch.address}</p>

          <dl>
            <div>
              <dt>Opening hours</dt>
              <dd>
                {formatOpeningDays(branch.opening_days)} · {formatBranchTime(branch.opening_time)} - {formatBranchTime(branch.closing_time)}
              </dd>
            </div>
            <div>
              <dt>Telephone</dt>
              <dd>
                <a href={`tel:${branch.telephone_number}`}>{formatGhanaPhone(branch.telephone_number)}</a>
                {branch.secondary_telephone_number ? (
                  <>
                    <span> / </span>
                    <a href={`tel:${branch.secondary_telephone_number}`}>{formatGhanaPhone(branch.secondary_telephone_number)}</a>
                  </>
                ) : null}
              </dd>
            </div>
            <div>
              <dt>WhatsApp</dt>
              <dd>
                {branch.whatsapp_number ? (
                  <a href={whatsappUrl(branch.whatsapp_number)} target="_blank" rel="noreferrer">
                    {formatGhanaPhone(branch.whatsapp_number)}
                  </a>
                ) : "Not provided"}
              </dd>
            </div>
            <div>
              <dt>Branch manager</dt>
              <dd>{branch.assigned_manager?.full_name ?? "Not assigned"}</dd>
            </div>
          </dl>
          <div className="management-branch-card__actions">
            <ButtonLink href={`/management/branches/${branch.id}`} variant="outline" size="small">
              View and edit
            </ButtonLink>
          </div>
        </article>
      ))}
    </div>
  );
}
