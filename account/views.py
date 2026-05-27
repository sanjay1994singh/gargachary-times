from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from account.models import User
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth import logout
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
        'account/register.html'
    )


def login_view(request):
    if request.method == 'POST':

        username = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        user = authenticate(

            request,

            username=username,

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
        'login.html'
    )


def logout_view(request):
    logout(request)

    return redirect('/')
