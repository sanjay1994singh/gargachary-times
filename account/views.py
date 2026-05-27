from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from account.models import User
from django.shortcuts import redirect
from django.contrib import messages


def register(request):
    if request.method == 'POST':

        username = request.POST.get(
            'username'
        )

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

        password = request.POST.get(
            'password'
        )

        confirm_password = request.POST.get(
            'confirm_password'
        )

        if password != confirm_password:
            messages.error(
                request,
                'Passwords do not match'
            )

            return redirect('register')

        if User.objects.filter(
                username=username
        ).exists():
            messages.error(
                request,
                'Username already exists'
            )

            return redirect('register')

        user = User.objects.create_user(

            username=username,

            email=email,

            mobile=mobile,

            city=city,

            district=district,

            state=state,

            password=password
        )

        login(
            request,
            user
        )

        return redirect('profile')

    return render(
        request,
        'register.html'
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

                return redirect('profile')

        return render(

            request,

            'login.html',

            {
                'error':
                    'Invalid login credentials'
            }
        )

    return render(
        request,
        'login.html'
    )


def logout_view(request):
    logout(request)

    return redirect('/')
