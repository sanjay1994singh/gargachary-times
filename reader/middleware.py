from django.utils.cache import patch_cache_control


class EpaperMediaCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.method in {"GET", "HEAD"}
            and response.status_code == 200
            and request.path.startswith("/media/editions/")
        ):
            patch_cache_control(
                response,
                public=True,
                max_age=60 * 60 * 24 * 365,
                immutable=True,
            )

        return response
