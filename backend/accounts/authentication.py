from rest_framework.authentication import SessionAuthentication
from rest_framework.request import Request


class CsrfProtectedSessionAuthentication(SessionAuthentication):
    """Enforce CSRF for every unsafe browser API request, including anonymous ones.

    DRF's default session authentication checks CSRF only after it finds an
    authenticated user. Login, registration, and other anonymous mutations
    therefore need this stricter boundary protection.
    """

    safe_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}

    def authenticate(self, request: Request):
        if request.method.upper() not in self.safe_methods:
            self.enforce_csrf(request)

        user = getattr(request._request, "user", None)
        if not user or not user.is_active:
            return None
        return user, None
