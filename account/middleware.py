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
            messages.error(
                request,
                'This Google account is already connected with another user. Please login with your email/mobile or use a different Google account.'
            )
            return redirect('login')
