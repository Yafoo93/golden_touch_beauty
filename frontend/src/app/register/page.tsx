import type { Metadata } from "next";
import { RegisterForm } from "@/components/auth/register-form";

export const metadata: Metadata = { title: "Create Account" };

export default function RegisterPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <p>Create your account</p>
        <h1>Join Golden Touch</h1>
        <span>Book services, track appointments, and keep your shopping details together.</span>
      </section>
      <RegisterForm />
    </main>
  );
}
