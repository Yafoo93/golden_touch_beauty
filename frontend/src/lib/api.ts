export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    status: number;
    details: unknown;
    request_id?: string;
  };
};

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: unknown;
  readonly requestId?: string;

  constructor(body: ApiErrorBody) {
    super(body.error.message);
    this.name = "ApiError";
    this.code = body.error.code;
    this.status = body.error.status;
    this.details = body.error.details;
    this.requestId = body.error.request_id;
  }
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  if (!value || typeof value !== "object" || !("error" in value)) {
    return false;
  }

  const error = (value as { error: unknown }).error;
  return Boolean(
    error &&
      typeof error === "object" &&
      "code" in error &&
      "message" in error &&
      "status" in error,
  );
}

function getCookie(name: string) {
  if (typeof document === "undefined") return undefined;
  const prefix = `${encodeURIComponent(name)}=`;
  const cookie = document.cookie.split("; ").find((item) => item.startsWith(prefix));
  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : undefined;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const normalizedPath = path.replace(/^\/+|\/+$/g, "");
  const timeoutController = new AbortController();
  const timeoutId = setTimeout(() => timeoutController.abort(), 15_000);
  const method = (init.method ?? "GET").toUpperCase();
  const csrfToken = ["POST", "PUT", "PATCH", "DELETE"].includes(method)
    ? getCookie("csrftoken")
    : undefined;

  let response: Response;
  try {
    response = await fetch(`/backend-api/v1/${normalizedPath}`, {
      ...init,
      credentials: "include",
      signal: init.signal ?? timeoutController.signal,
      headers: {
        Accept: "application/json",
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        ...init.headers,
      },
    });
  } finally {
    clearTimeout(timeoutId);
  }

  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    if (isApiErrorBody(body)) {
      throw new ApiError(body);
    }

    throw new ApiError({
      error: {
        code: "invalid_error_response",
        message: "The server returned an unreadable error response.",
        status: response.status,
        details: body,
      },
    });
  }

  return body as T;
}

export async function ensureCsrfCookie() {
  await apiFetch<{ detail: string }>("auth/csrf/");
}
