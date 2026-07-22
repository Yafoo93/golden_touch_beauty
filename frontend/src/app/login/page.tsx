import type { Metadata } from "next";
import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = { title: "Sign In" };

export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <p>Customer and staff access</p>
        <h1>Welcome back</h1>
        <span>Sign in using the email address or phone number connected to your account.</span>
      </section>
      <LoginForm />
    </main>
  );
}
