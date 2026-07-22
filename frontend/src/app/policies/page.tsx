import type { Metadata } from "next";

export const metadata: Metadata = { title: "Terms and Privacy" };

export default function PoliciesPage() {
  return (
    <main className="policy-page">
      <header><p>Golden Touch policies</p><h1>Terms and Privacy</h1><span>Development draft · Legal review is required before production launch.</span></header>
      <section id="terms"><h2>Terms and Conditions</h2><p>Customers must provide accurate account and booking information, protect their credentials, and use the platform lawfully. Appointments remain subject to branch availability and management confirmation. Product orders remain subject to stock, price, payment, and fulfilment confirmation.</p><p>Service information does not replace medical advice. Customers should disclose relevant treatment information, allergies, medication, pregnancy, or previous reactions when requested.</p></section>
      <section id="privacy"><h2>Privacy Policy</h2><p>Golden Touch uses identity, contact, booking, order, payment, and security information to operate customer accounts and deliver requested services. Passwords are stored as secure hashes, and raw payment-card details must not be stored by Golden Touch.</p><p>Marketing consent is optional and separate from operational communication. Customers may withdraw future marketing consent. Final retention periods, privacy contacts, complaint procedures, and regulator information require approval before launch.</p></section>
    </main>
  );
}
