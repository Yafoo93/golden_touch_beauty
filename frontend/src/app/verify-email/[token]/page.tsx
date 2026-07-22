import type { Metadata } from "next";
import { EmailVerificationResult } from "@/components/auth/email-verification-result";

export const metadata: Metadata = { title: "Email Verification" };

export default async function EmailVerificationPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <p>Account security</p>
        <h1>Email verification</h1>
        <span>We are securely confirming the email address associated with your Golden Touch account.</span>
      </section>
      <EmailVerificationResult token={token} />
    </main>
  );
}
