from django.conf import settings
from django.shortcuts import redirect


class HttpRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            if request.headers.get("X-Forwarded-Proto", "") == 'http':
                path = 'https://'
                path += request.META.get('HTTP_HOST')
                path += request.get_full_path()
                return redirect(path)

        response = self.get_response(request)

        return response


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        response["Access-Control-Allow-Origin"] = "*"

        return response
