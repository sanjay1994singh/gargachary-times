from django.utils.cache import patch_cache_control


class HtmlNoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        content_type = response.get('Content-Type', '')

        if (
            request.method in {'GET', 'HEAD'}
            and response.status_code == 200
            and content_type.startswith('text/html')
        ):
            patch_cache_control(
                response,
                no_cache=True,
                must_revalidate=True,
            )
            response['Pragma'] = 'no-cache'

        return response
