from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from account.models import User
from django.http import JsonResponse


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
