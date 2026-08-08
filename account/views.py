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


def register(request):
    if request.method == 'POST':

        email = request.POST.get(
            'email'
        )

        mobile = request.POST.get(
            'mobile'
        )

        city = request.POST.get(
            'city'
        )

        district = request.POST.get(
            'district'
        )

        state = request.POST.get(
            'state'
        )

        address = request.POST.get(
            'address'
        )

        pincode = request.POST.get(
            'pincode'
        )

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

        user = User.objects.create_user(

            username=username,

            email=email,

            mobile=mobile,

            full_name=request.POST.get('full_name'),

            address=address,

            city=city,

            district=district,

            state=state,

            pincode=pincode,

            country=request.POST.get('country') or 'India',

            password=password
        )

        send_account_created_email(user, password)

        login(
            request,
            user
        )

        return redirect('profile')

    return render(
        request,
        'register.html',
        {
            'states': State.objects.filter(country__code='IN'),
            'default_state': 'Uttar Pradesh',
        }
    )


def login_view(request):
    if request.method == 'POST':

        username_input = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        user_obj = User.objects.filter(

            mobile=username_input

        ).first()

        if not user_obj:
            user_obj = User.objects.filter(

                email=username_input

            ).first()

        if not user_obj:
            user_obj = User.objects.filter(

                username=username_input

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

        return render(

            request,

            'login.html',

            {
                'error':
                    'Invalid login credentials',
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
