import type { Metadata } from "next";
import { ResetPasswordForm } from "@/components/auth/reset-password-form";

export const metadata: Metadata = { title: "Choose a New Password" };

export default async function ResetPasswordPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <p>Account recovery</p>
        <h1>Choose a new password</h1>
        <span>Enter a strong password you have not used for this account before.</span>
      </section>
      <ResetPasswordForm token={token} />
    </main>
  );
}
