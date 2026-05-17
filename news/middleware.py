from .models import Visitor
import requests

class VisitorMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        ip = self.get_client_ip(request)

        Visitor.objects.create(
            ip_address=ip
        )

        response = self.get_response(request)

        return response

    def get_client_ip(self, request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        return ip

    def save_visitor(request):

        ip = get_client_ip(request)

        try:

            response = requests.get(
                f'https://ipapi.co/{ip}/json/'
            ).json()

            city = response.get('city')

            state = response.get('region')

            country = response.get('country_name')

        except:

            city = None
            state = None
            country = None

        Visitor.objects.create(

            ip_address=ip,

            city=city,

            state=state,

            country=country

        )
