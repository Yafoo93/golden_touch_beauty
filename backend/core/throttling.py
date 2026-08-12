from rest_framework.throttling import ScopedRateThrottle


class UnsafeMethodScopedRateThrottle(ScopedRateThrottle):
    """Apply a shared scope only to state-changing requests."""

    def allow_request(self, request, view):
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return True
        return super().allow_request(request, view)

