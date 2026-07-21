"use client";

import { useEffect } from "react";

import { reportClientError, type ReportableError } from "@/lib/error-reporting";
import "./globals.css";

export default function GlobalError({
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
    <html lang="en">
      <body className="global-error-body">
        <title>Application error | Golden Touch Beauty Centre</title>
        <main className="global-error-card" role="alert">
          <p>Something went wrong</p>
          <h1>Golden Touch is temporarily unavailable.</h1>
          <p>Please try again in a moment.</p>
          {error.digest ? <small>Reference: {error.digest}</small> : null}
          <button type="button" onClick={() => unstable_retry()}>
            Try again
          </button>
        </main>
      </body>
    </html>
  );
}
