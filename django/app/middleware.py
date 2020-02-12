from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth import logout


class HttpRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            if request.headers.get("X-Forwarded-Proto", "") == "http":
                path = "https://"
                path += request.META.get("HTTP_HOST")
                path += request.get_full_path()
                return redirect(path)

        response = self.get_response(request)

        return response


class AutoLogout:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logout_at = request.session.get("logout_at", None)
        if logout_at is not None:
            if (
                timezone.now() - timezone.datetime.fromisoformat(logout_at)
            ).total_seconds() > 0:
                logout(request)

        response = self.get_response(request)

        return response


class DisableCSRF(MiddlewareMixin):
    def process_request(self, request):
        setattr(request, "_dont_enforce_csrf_checks", True)
