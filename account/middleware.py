from django.contrib import messages
from django.shortcuts import redirect
from social_core.exceptions import SocialAuthBaseException


class SocialAuthErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except SocialAuthBaseException:
            messages.warning(
                request,
                'This email is already registered. Please login with your email/mobile password.'
            )
            return redirect('login')
