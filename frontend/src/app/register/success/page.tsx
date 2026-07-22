import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui/button";

export const metadata: Metadata = { title: "Account Created" };

export default function RegistrationSuccessPage() {
  return (
    <main className="auth-page">
      <section className="auth-success" role="status">
        <span className="auth-success__icon" aria-hidden="true">✓</span>
        <h1>Account created</h1>
        <p>Your Golden Touch customer account has been created. Verify your email address to finish securing your account.</p>
        <ButtonLink href="/verify-email" fullWidth>Verify email address</ButtonLink>
        <ButtonLink href="/book" variant="outline" fullWidth>Book an appointment</ButtonLink>
        <ButtonLink href="/" variant="outline" fullWidth>Return home</ButtonLink>
      </section>
    </main>
  );
}
