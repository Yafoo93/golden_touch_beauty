import type { Instrumentation } from "next";

export const onRequestError: Instrumentation.onRequestError = (
  error,
  request,
  context,
) => {
  const message = error instanceof Error ? error.message : String(error);
  const digest =
    typeof error === "object" && error !== null && "digest" in error
      ? String(error.digest)
      : undefined;

  console.error(
    JSON.stringify({
      timestamp: new Date().toISOString(),
      level: "ERROR",
      logger: "golden-touch.frontend",
      message: "next_request_failed",
      error_message: message,
      error_digest: digest,
      method: request.method,
      path: request.path,
      route_path: context.routePath,
      route_type: context.routeType,
    }),
  );
};
