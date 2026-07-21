export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    status: number;
    details: unknown;
  };
};

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: unknown;

  constructor(body: ApiErrorBody) {
    super(body.error.message);
    this.name = "ApiError";
    this.code = body.error.code;
    this.status = body.error.status;
    this.details = body.error.details;
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

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/backend-api/v1/${path.replace(/^\//, "")}`, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...init.headers,
    },
  });

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
