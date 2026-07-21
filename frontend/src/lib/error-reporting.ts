export type ReportableError = Error & { digest?: string };

export async function reportClientError(error: ReportableError): Promise<void> {
  const payload = {
    name: error.name.slice(0, 100),
    message: error.message.slice(0, 500),
    digest: error.digest?.slice(0, 200) ?? "",
    path: window.location.pathname.slice(0, 500),
  };

  try {
    await fetch("/backend-api/v1/client-errors/", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
    });
  } catch {
    // The fallback stays local if the reporting endpoint is unavailable.
    console.error("Unable to report client error", payload);
  }
}
