import type { Metadata } from "next";
import { VerifyEmailForm } from "@/components/auth/verify-email-form";

export const metadata: Metadata = { title: "Verify Your Email" };

export default function VerifyEmailPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <p>Protect your account</p>
        <h1>Verify your email</h1>
        <span>Email verification confirms that you control the address connected to your account. It helps secure account recovery, booking notices, order updates, and receipts.</span>
      </section>
      <VerifyEmailForm />
    </main>
  );
}
