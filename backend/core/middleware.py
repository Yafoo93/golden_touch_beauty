import logging
import time
import uuid

from .logging import request_id_context


logger = logging.getLogger("golden_touch.requests")


class RequestLoggingMiddleware:
    """Attach a correlation ID and record one safe summary per HTTP request."""

    header_name = "HTTP_X_REQUEST_ID"
    response_header = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        supplied_id = request.META.get(self.header_name, "")
        request_id = (
            supplied_id
            if self._is_valid_request_id(supplied_id)
            else str(uuid.uuid4())
        )
        request.request_id = request_id
        token = request_id_context.set(request_id)
        started_at = time.perf_counter()

        try:
            response = self.get_response(request)
        except Exception:
            logger.exception(
                "request_failed",
                extra=self._context(request, 500, started_at),
            )
            raise
        else:
            level = logging.ERROR if response.status_code >= 500 else logging.INFO
            logger.log(
                level,
                "request_completed",
                extra=self._context(request, response.status_code, started_at),
            )
            response[self.response_header] = request_id
            return response
        finally:
            request_id_context.reset(token)

    @staticmethod
    def _is_valid_request_id(value):
        return bool(value) and len(value) <= 100 and all(
            character.isalnum() or character in "-_." for character in value
        )

    @staticmethod
    def _context(request, status_code, started_at):
        user = getattr(request, "user", None)
        return {
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "status_code": status_code,
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "user_id": str(user.pk) if getattr(user, "is_authenticated", False) else None,
        }
