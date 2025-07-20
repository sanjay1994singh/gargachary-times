from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from account.models import User
from django.http import JsonResponse
from django.shortcuts import redirect


# Create your views here.
def user_login(request):
    if request.method == 'POST':
        mobile = request.POST.get('mobile')
        mobile = mobile[-10:]
        password = request.POST.get('password')
        status = 'failed'
        msg = 'Account does not exist for this number, please enter the correct mobile number.'

        try:
            user = User.objects.filter(mobile__iexact=mobile)
            user_name = user[0].username
            user = authenticate(username=user_name, password=password)
            if user is not None:
                login(request, user)
                request.session['user_id'] = user.id
                status = 'success'
                msg = 'Login successful.'
            else:
                msg = 'Invalid password.'
        except User.DoesNotExist:
            msg = msg
        except Exception as e:
            msg = str(e)

        context = {
            'status': status,
            'msg': msg,
        }
        return JsonResponse(context)
    return render(request, 'user_login.html')


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('/account/reporter-user-login/')


def register_new_report(request):
    if request.method == 'POST':
        form = request.POST
        first_name = form.get('fullname')
        first_name.strip()

        username = form.get('mobile')
        username.strip()
        username = username[-10:]

        email = form.get('email')
        email.strip()

        password = form.get('password')
        password = password.strip()

        city = form.get('city')
        district = form.get('district')
        state = form.get('state')
        contact_number = form.get('mobile')
        query = Q(username=username) | Q(email=email) | Q(mobile=contact_number)
        id = 0
        msg = ''
        status = 'failed!'
        try:
            user = User.objects.filter(query).exists()
            if user:
                msg = 'This User Already Exists.'
                data_json = {
                    'id': id,
                    'msg': msg,
                }

                return JsonResponse(data_json)
            user = User.objects.create_user(username)
            if user is not None:
                user.set_password(password)
                user.first_name = first_name
                user.email = email
                user.mobile = contact_number
                user.city = city
                user.district = district
                user.state = state
                user.save()
                msg = 'User registration successfully.'
                status = 'success'
        except Exception as e:
            msg = str(e)

        data_json = {
            'id': id,
            'msg': msg,
            'status': status,
        }

        return JsonResponse(data_json)

    else:
        return render(request, 'register_reporter.html')


def update_password(request):
    if request.method == 'POST':
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        user = User.objects.get(username=mobile)
        user.set_password('password')
        user.save()
        msg = 'This User Already Exists.'
        data_json = {
            'id': id,
            'msg': msg,
        }

        return JsonResponse(data_json)
    else:
        return render(request, 'update_password.html')
