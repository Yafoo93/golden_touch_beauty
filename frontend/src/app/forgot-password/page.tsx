import type { Metadata } from "next";
import { ForgotPasswordForm } from "@/components/auth/forgot-password-form";

export const metadata: Metadata = { title: "Forgot Password" };

export default function ForgotPasswordPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <p>Account recovery</p>
        <h1>Reset your password</h1>
        <span>Enter your account email and we’ll send instructions if the account is active.</span>
      </section>
      <ForgotPasswordForm />
    </main>
  );
}
