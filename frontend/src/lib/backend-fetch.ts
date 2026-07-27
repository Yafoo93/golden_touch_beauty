const DEFAULT_ATTEMPTS = 3;
const DEFAULT_TIMEOUT_MS = 20_000;
const RETRY_DELAYS_MS = [1_000, 2_000];

function shouldRetry(status: number) {
  return status === 408 || status === 425 || status === 429 || status >= 500;
}

function wait(milliseconds: number) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

/**
 * Fetch JSON from Django while allowing a sleeping development backend time to
 * wake. Responses are deliberately not cached so a cold-start failure cannot
 * become the catalogue response served to later visitors.
 */
export async function fetchBackendJson<T>(
  url: string,
  {
    attempts = DEFAULT_ATTEMPTS,
    timeoutMs = DEFAULT_TIMEOUT_MS,
  }: {
    attempts?: number;
    timeoutMs?: number;
  } = {},
): Promise<T | null> {
  const totalAttempts = Math.max(1, attempts);

  for (let attempt = 0; attempt < totalAttempts; attempt += 1) {
    try {
      const response = await fetch(url, {
        cache: "no-store",
        headers: { Accept: "application/json" },
        signal: AbortSignal.timeout(timeoutMs),
      });

      if (response.ok) {
        return (await response.json()) as T;
      }

      if (!shouldRetry(response.status)) {
        return null;
      }
    } catch {
      // Network errors and timeouts are retried below.
    }

    if (attempt < totalAttempts - 1) {
      await wait(RETRY_DELAYS_MS[attempt] ?? RETRY_DELAYS_MS.at(-1) ?? 1_000);
    }
  }

  return null;
}
