import { ButtonLink } from "@/components/ui/button";
import { formatGhanaPhone, whatsappUrl } from "@/lib/branch-formatters";

export type StaffWhatsAppAction = {
  label: string;
  message: string;
};

type StaffWhatsAppActionsProps = {
  phoneNumber: string;
  recipientName: string;
  actions: StaffWhatsAppAction[];
};

export function StaffWhatsAppActions({
  phoneNumber,
  recipientName,
  actions,
}: StaffWhatsAppActionsProps) {
  const digits = phoneNumber.replace(/\D/g, "");

  return (
    <section className="staff-whatsapp-actions">
      <div>
        <p>Customer communication</p>
        <h2>WhatsApp actions</h2>
        <span>
          Messages open in WhatsApp for review before sending to {recipientName}.
        </span>
      </div>
      {digits ? (
        <>
          <p>
            WhatsApp number: <strong>{formatGhanaPhone(phoneNumber)}</strong>
          </p>
          <div className="staff-whatsapp-actions__buttons">
            {actions.map((action, index) => (
              <ButtonLink
                href={whatsappUrl(phoneNumber, action.message)}
                key={`${action.label}-${index}`}
                target="_blank"
                rel="noreferrer"
                variant={index === 0 ? "gold" : "outline"}
                size="small"
                aria-label={`${action.label} on WhatsApp`}
              >
                {action.label}
              </ButtonLink>
            ))}
          </div>
          <small>
            Confirm the recipient and wording in WhatsApp before sending. Private
            consultation details are intentionally excluded.
          </small>
        </>
      ) : (
        <p>No valid customer phone number is available for WhatsApp.</p>
      )}
    </section>
  );
}
