"use client";

import { useEffect } from "react";

import { reportClientError, type ReportableError } from "@/lib/error-reporting";

export default function ErrorPage({
  error,
  unstable_retry,
}: {
  error: ReportableError;
  unstable_retry: () => void;
}) {
  useEffect(() => {
    void reportClientError(error);
  }, [error]);

  return (
    <main className="error-shell">
      <section className="error-card" role="alert">
        <p className="error-eyebrow">Something went wrong</p>
        <h1>We could not load this page.</h1>
        <p>Please try again. If the problem continues, contact Golden Touch.</p>
        {error.digest ? <p className="error-reference">Reference: {error.digest}</p> : null}
        <button type="button" onClick={() => unstable_retry()}>
          Try again
        </button>
      </section>
    </main>
  );
}
