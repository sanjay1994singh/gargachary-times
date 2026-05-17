from .models import Visitor

import requests


class VisitorMiddleware:

    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        # Ignore admin and static files

        ignored_paths = [

            '/admin/',
            '/static/',
            '/media/'

        ]

        if any(

                request.path.startswith(path)

                for path in ignored_paths

        ):
            return self.get_response(request)

        self.save_visitor(request)

        response = self.get_response(request)

        return response

    def get_client_ip(self, request):

        x_forwarded_for = request.META.get(
            'HTTP_X_FORWARDED_FOR'
        )

        if x_forwarded_for:

            ip = x_forwarded_for.split(',')[0]

        else:

            ip = request.META.get('REMOTE_ADDR')

        return ip

    def save_visitor(self, request):

        ip = self.get_client_ip(request)

        # Prevent duplicate entry within same session

        session_key = f'visited_{ip}'

        if request.session.get(session_key):
            return

        try:

            response = requests.get(
                f'http://ip-api.com/json/{ip}',

                timeout=3

            ).json()

            city = response.get('city')

            state = response.get('region')

            country = response.get('country')


        except Exception:

            city = None
            state = None
            country = None

        Visitor.objects.create(

            ip_address=ip,

            city=city,

            state=state,

            country=country

        )

        request.session[session_key] = True
