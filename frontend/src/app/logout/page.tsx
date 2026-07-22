import type { Metadata } from "next";
import { LogoutAction } from "@/components/auth/logout-action";

export const metadata: Metadata = { title: "Signing Out" };

export default function LogoutPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <p>Account security</p>
        <h1>Signing out</h1>
        <span>Your server session is being closed before you return to the home page.</span>
      </section>
      <LogoutAction />
    </main>
  );
}
