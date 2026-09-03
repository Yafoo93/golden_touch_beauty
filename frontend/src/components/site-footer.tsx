"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import {
  formatBranchTime,
  formatGhanaPhone,
  formatOpeningDays,
  whatsappUrl,
} from "@/lib/branch-formatters";
import type { PaginatedResponse, PublicBranch } from "@/lib/branches";

const fallbackBranches: PublicBranch[] = [
  {
    id: "makola-fallback",
    code: "makola",
    name: "Makola",
    address: "Makola, Accra",
    telephone_number: "+233241370429",
    secondary_telephone_number: "+233257711182",
    whatsapp_number: "+233241370429",
    secondary_whatsapp_number: "+233257711182",
    email: "",
    google_maps_url:
      "https://maps.google.com/maps?vet=10CAAQoqAOahcKEwj4mrSs7c-VAxUAAAAAHQAAAAAQIg..i&pvq=CgwvZy8xaGRfbDdmN2Q&fvr=1&cs=0&um=1&ie=UTF-8&fb=1&gl=gh&sa=X&ftid=0xfdf90bdedf8501b:0x52470e6bd2670358",
    opening_days: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    opening_time: "07:30:00",
    closing_time: "17:00:00",
  },
  {
    id: "tse-addo-fallback",
    code: "tse-addo",
    name: "Tse Addo",
    address: "Tse Addo, Accra",
    telephone_number: "+233241370429",
    secondary_telephone_number: "+233207911043",
    whatsapp_number: "+233241370429",
    secondary_whatsapp_number: "+233207911043",
    email: "",
    google_maps_url: "",
    opening_days: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
    opening_time: "07:30:00",
    closing_time: "19:00:00",
  },
];

const explore = [
  { href: "/about", label: "About us" },
  { href: "/contact", label: "Contact and branches" },
  { href: "/gallery", label: "Gallery" },
  { href: "/bridal-packages", label: "Bridal packages" },
  { href: "/testimonials", label: "Testimonials" },
  { href: "/blog", label: "Beauty tips" },
  { href: "/faq", label: "Frequently asked questions" },
];

const policies = [
  { href: "/terms", label: "Terms of Use" },
  { href: "/privacy", label: "Privacy Policy" },
  { href: "/cancellation-refunds", label: "Cancellations & Refunds" },
  { href: "/delivery-returns", label: "Delivery & Returns" },
];

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

function InstagramIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4.25" />
      <circle cx="17.4" cy="6.7" r="0.75" fill="currentColor" stroke="none" />
    </svg>
  );
}

function TikTokIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M15 4v10.2a4.2 4.2 0 1 1-3.4-4.1" />
      <path d="M15 4c.6 2.5 2.1 3.9 4.5 4.3" />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M14.5 21v-8h2.8l.5-3.2h-3.3V7.7c0-.9.3-1.7 1.8-1.7H18V3.1c-.6-.1-1.4-.1-2.4-.1-2.5 0-4.2 1.5-4.2 4.4v2.4H8.5V13h2.9v8" />
    </svg>
  );
}

export function SiteFooter() {
  const pathname = usePathname();
  const [branches, setBranches] = useState(fallbackBranches);

  useEffect(() => {
    let cancelled = false;
    apiFetch<PaginatedResponse<PublicBranch>>("branches/")
      .then((response) => {
        if (!cancelled && response.results.length) setBranches(response.results);
      })
      .catch(() => {
        // Keep the development fallback visible while Django wakes or is offline.
      });
    return () => {
      cancelled = true;
    };
  }, [pathname]);

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
          <div
            className="site-footer__socials"
            aria-label="Golden Touch social media and WhatsApp contacts"
          >
            <a
              href="https://www.instagram.com/golden_touch_beauty_center?igsi=N2h3YnZwazZmYWlv"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Follow Golden Touch Beauty Centre on Instagram"
            >
              <InstagramIcon />
              Instagram
            </a>
            <a
              href="https://www.tiktok.com/@marcelwaygma?_r=1&_t=ZS-99KI9DifbQS"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Follow Golden Touch Beauty Centre on TikTok"
            >
              <TikTokIcon />
              TikTok
            </a>
            <a
              href="https://www.facebook.com/share/1ByZUTLR6G/?mibextid=wwXIfr"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Follow Golden Touch Beauty Centre on Facebook"
            >
              <FacebookIcon />
              Facebook
            </a>
            <a
              href="https://wa.me/233241370429"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Chat with Golden Touch on WhatsApp at +233 241 370 429"
            >
              <WhatsAppIcon />
              WhatsApp 1
            </a>
            <a
              href="https://wa.me/233257711182"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Chat with Golden Touch on WhatsApp at +233 257 711 182"
            >
              <WhatsAppIcon />
              WhatsApp 2
            </a>
          </div>
        </section>

        {branches.map((branch) => (
          <section className="site-footer__branch" key={branch.id}>
            <h2>{branch.name}</h2>
            <p className="site-footer__hours">
              {formatOpeningDays(branch.opening_days)},{" "}
              {formatBranchTime(branch.opening_time)} -{" "}
              {formatBranchTime(branch.closing_time)}
            </p>
            <ul>
              {[
                {
                  phone: branch.telephone_number,
                  whatsapp: branch.whatsapp_number,
                },
                {
                  phone: branch.secondary_telephone_number,
                  whatsapp: branch.secondary_whatsapp_number,
                },
              ].filter((contact) => contact.phone).map((contact) => (
                <li key={contact.phone}>
                  <PhoneIcon />
                  <a href={`tel:${contact.phone}`}>
                    {formatGhanaPhone(contact.phone)}
                  </a>
                  {contact.whatsapp ? (
                    <a
                      className="site-footer__whatsapp-link"
                      href={whatsappUrl(contact.whatsapp)}
                      target="_blank"
                      rel="noreferrer"
                      aria-label={`WhatsApp ${formatGhanaPhone(contact.whatsapp)}`}
                    >
                      WhatsApp
                    </a>
                  ) : null}
                </li>
              ))}
            </ul>
            {branch.google_maps_url ? (
              <a
                className="site-footer__map"
                href={branch.google_maps_url}
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

        <nav className="site-footer__policies" aria-label="Explore">
          <h2>Explore</h2>
          {explore.map((item) => (
            <Link href={item.href} key={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>

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
