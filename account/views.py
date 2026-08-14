import secrets
import string

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from account.models import State, User
from django.shortcuts import redirect
from django.contrib import messages
from social_core.exceptions import SocialAuthBaseException
from social_django.views import complete


def generate_strong_password(length=14):
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'

    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))

        if (
            any(char.islower() for char in password) and
            any(char.isupper() for char in password) and
            any(char.isdigit() for char in password) and
            any(char in '!@#$%^&*' for char in password)
        ):
            return password


def send_account_created_email(user, password):
    if not user.email:
        return

    context = {
        'user': user,
        'password': password,
        'login_url': f'{settings.BASE_URL}/login/',
        'site_url': settings.BASE_URL,
    }
    subject = 'Your Gargachary Times account is ready'
    text_body = render_to_string(
        'emails/account_created.txt',
        context
    )
    html_body = render_to_string(
        'emails/account_created.html',
        context
    )

    email = EmailMultiAlternatives(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_body, 'text/html')
    email.send(fail_silently=True)


def google_oauth_complete(request):
    try:
        return complete(request, backend='google-oauth2')
    except SocialAuthBaseException:
        messages.warning(
            request,
            'This email is already registered. Please login with your email/mobile password.'
        )
        return redirect('login')


def register(request):
    if request.method == 'POST':
        first_name = (
            request.POST.get('first_name') or ''
        ).strip()

        last_name = (
            request.POST.get('last_name') or ''
        ).strip()

        email = request.POST.get(
            'email'
        ).strip()

        mobile = request.POST.get(
            'mobile'
        ).strip()

        city = request.POST.get(
            'city'
        ).strip()

        district = request.POST.get(
            'district'
        ).strip()

        state = request.POST.get(
            'state'
        ).strip()

        address = request.POST.get(
            'address'
        ).strip()

        pincode = request.POST.get(
            'pincode'
        ).strip()

        country = (
            request.POST.get('country') or 'India'
        ).strip()

        user_type = (
            request.POST.get('user_type') or ''
        ).strip()

        allowed_user_types = {
            'subscriber',
            'reporter'
        }

        required_values = (
            first_name,
            last_name,
            email,
            mobile,
            city,
            state,
            address,
            pincode,
            country,
            user_type
        )

        if not all(required_values):
            messages.error(
                request,
                'All fields are required.'
            )

            return redirect('register')

        if user_type not in allowed_user_types:
            messages.error(
                request,
                'Please select a valid user type.'
            )

            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(
                request,
                'Email already exists'
            )

            return redirect('register')

        if mobile and User.objects.filter(mobile=mobile).exists():
            messages.error(
                request,
                'Mobile already exists'
            )

            return redirect('register')

        password = generate_strong_password()
        username = email or mobile
        full_name = f'{first_name} {last_name}'.strip()

        user = User.objects.create_user(

            username=username,

            email=email,

            mobile=mobile,

            first_name=first_name,

            last_name=last_name,

            full_name=full_name,

            user_type=user_type,

            address=address,

            city=city,

            district=district,

            state=state,

            pincode=pincode,

            country=country,

            password=password
        )

        send_account_created_email(user, password)

        login(
            request,
            user,
            backend='django.contrib.auth.backends.ModelBackend'
        )

        messages.success(
            request,
            'Account created successfully. Login details have been sent to your email.'
        )

        return redirect('profile')

    return render(
        request,
        'register.html',
        {
            'account_states': State.objects.filter(country__code='IN'),
            'default_state': 'Uttar Pradesh',
        }
    )


def login_view(request):
    if request.method == 'POST':

        username_input = request.POST.get(
            'username'
        )
        username_input = (username_input or '').strip()

        password = request.POST.get(
            'password'
        )

        user_obj = User.objects.filter(

            mobile=username_input

        ).first()

        if not user_obj:
            user_obj = User.objects.filter(

                email__iexact=username_input

            ).first()

        if not user_obj:
            user_obj = User.objects.filter(

                username__iexact=username_input

            ).first()

        if user_obj:

            user = authenticate(

                request,

                username=user_obj.username,

                password=password
            )

            if user:
                login(
                    request,
                    user
                )

                return redirect(
                    request.POST.get('next') or
                    request.GET.get('next') or
                    'profile'
                )

        messages.error(
            request,
            'Invalid login credentials'
        )

        return render(

            request,

            'login.html',

            {
                'next': request.POST.get('next', '')
            }
        )

    return render(
        request,
        'login.html',
        {
            'next': request.GET.get('next', '')
        }
    )


def logout_view(request):
    logout(request)

    return redirect('/')
