import Image from "next/image";
import Link from "next/link";

const makolaMapUrl =
  "https://maps.google.com/maps?vet=10CAAQoqAOahcKEwj4mrSs7c-VAxUAAAAAHQAAAAAQIg..i&pvq=CgwvZy8xaGRfbDdmN2Q&fvr=1&cs=0&um=1&ie=UTF-8&fb=1&gl=gh&sa=X&ftid=0xfdf90bdedf8501b:0x52470e6bd2670358";

const branches = [
  {
    name: "Makola",
    hours: "Monday - Saturday, 7:30 AM - 5:00 PM",
    contacts: ["233241370429", "233257711182"],
    mapUrl: makolaMapUrl,
  },
  {
    name: "Tse Addo",
    hours: "Monday - Saturday, 7:30 AM - 7:00 PM",
    contacts: ["233241370429", "233207911043"],
    mapUrl: null,
  },
];

const policies = [
  { href: "/policies/terms", label: "Terms of Use" },
  { href: "/policies/privacy", label: "Privacy Policy" },
  { href: "/policies/cancellations-refunds", label: "Cancellations & Refunds" },
  { href: "/policies/delivery-returns", label: "Delivery & Returns" },
];

function formatPhone(number: string) {
  return `+${number.slice(0, 3)} ${number.slice(3, 6)} ${number.slice(6, 9)} ${number.slice(9)}`;
}

function PhoneIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6.7 3.8 9 3.2l2.1 5-1.8 1.4a14.6 14.6 0 0 0 5.1 5.1l1.4-1.8 5 2.1-.6 2.3a3 3 0 0 1-3.3 2.3A15.8 15.8 0 0 1 4.4 7.1 3 3 0 0 1 6.7 3.8Z" />
    </svg>
  );
}

function LocationIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}

function WhatsAppIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20.5 11.7a8.5 8.5 0 0 1-12.6 7.5L3 20.5l1.3-4.7a8.5 8.5 0 1 1 16.2-4.1Z" />
      <path d="M8.2 7.8c.3 4 3.1 6.8 7 7.1l1-1.7-2.3-1.1-.9 1a6.5 6.5 0 0 1-2.3-2.2l1-1-1.1-2.2-1.4.1Z" />
    </svg>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <section className="site-footer__brand" aria-labelledby="footer-brand-title">
          <div className="site-footer__brand-heading">
            <Image
              src="/images/logo.png"
              alt=""
              width={56}
              height={56}
              className="site-footer__logo"
            />
            <div>
              <p className="site-footer__eyebrow">Golden Touch</p>
              <h2 id="footer-brand-title">Beauty Centre</h2>
            </div>
          </div>
          <p>
            Professional beauty, wellness, and personal-care services across
            our Ghana branches.
          </p>
          <div className="site-footer__socials" aria-label="WhatsApp contacts">
            <a
              href="https://wa.me/233241370429"
              target="_blank"
              rel="noreferrer"
              aria-label="Chat with Golden Touch on WhatsApp at +233 241 370 429"
            >
              <WhatsAppIcon />
              WhatsApp 1
            </a>
            <a
              href="https://wa.me/233257711182"
              target="_blank"
              rel="noreferrer"
              aria-label="Chat with Golden Touch on WhatsApp at +233 257 711 182"
            >
              <WhatsAppIcon />
              WhatsApp 2
            </a>
          </div>
        </section>

        {branches.map((branch) => (
          <section className="site-footer__branch" key={branch.name}>
            <h2>{branch.name}</h2>
            <p className="site-footer__hours">{branch.hours}</p>
            <ul>
              {branch.contacts.map((contact) => (
                <li key={contact}>
                  <PhoneIcon />
                  <a href={`tel:+${contact}`}>{formatPhone(contact)}</a>
                  <a
                    className="site-footer__whatsapp-link"
                    href={`https://wa.me/${contact}`}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`WhatsApp ${formatPhone(contact)}`}
                  >
                    WhatsApp
                  </a>
                </li>
              ))}
            </ul>
            {branch.mapUrl ? (
              <a
                className="site-footer__map"
                href={branch.mapUrl}
                target="_blank"
                rel="noreferrer"
              >
                <LocationIcon />
                View on Google Maps
              </a>
            ) : (
              <p className="site-footer__map-unavailable">
                <LocationIcon />
                Map link coming soon
              </p>
            )}
          </section>
        ))}

        <nav className="site-footer__policies" aria-label="Policies">
          <h2>Policies</h2>
          {policies.map((policy) => (
            <Link href={policy.href} key={policy.href}>
              {policy.label}
            </Link>
          ))}
        </nav>
      </div>

      <div className="site-footer__bottom">
        <p>&copy; {new Date().getFullYear()} Golden Touch Beauty Centre.</p>
        <p>Serving clients in Accra, Ghana.</p>
      </div>
    </footer>
  );
}
