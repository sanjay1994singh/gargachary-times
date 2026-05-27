import uuid
import json
import base64
import hashlib
import requests

from django.conf import settings
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib.auth.decorators import (
    login_required
)

from django.urls import reverse

from django.utils import timezone

from django.db.models import Q

from .models import (
    SubscriptionPlan,
    UserSubscription,
    EPaper
)


# SUBSCRIPTION PLANS PAGE

def plans(request):
    plans = (SubscriptionPlan.objects.filter(is_active=True).order_by('price'))

    context = {
        'plans': plans
    }

    return render(
        request,
        'subscriptions/plans.html',
        context
    )


# SUBSCRIBE PAGE

@login_required
def subscribe(request, plan_id):
    plan = get_object_or_404(
        SubscriptionPlan,
        id=plan_id,
        is_active=True
    )

    context = {
        'plan': plan
    }

    return render(
        request,
        'subscriptions/subscribe.html',
        context
    )


# PHONEPE PAYMENT

@login_required
def phonepe_payment(request, plan_id):
    plan = get_object_or_404(
        SubscriptionPlan,
        id=plan_id
    )

    transaction_id = str(uuid.uuid4())

    subscription = (
        UserSubscription.objects.create(

            user=request.user,

            plan=plan,

            amount=plan.price,

            transaction_id=transaction_id,

            payment_status='PENDING'
        )
    )

    callback_url = (
        request.build_absolute_uri(
            reverse('payment_callback')
        )
    )

    payload = {

        "merchantId":
            settings.PHONEPE_MERCHANT_ID,

        "merchantTransactionId":
            transaction_id,

        "merchantUserId":
            str(request.user.id),

        "amount":
            int(plan.price * 100),

        "redirectUrl":
            callback_url,

        "redirectMode":
            "POST",

        "callbackUrl":
            callback_url,

        "mobileNumber":
            request.user.mobile or "9999999999",

        "paymentInstrument": {
            "type": "PAY_PAGE"
        }
    }

    endpoint = "/pg/v1/pay"

    payload_string = json.dumps(payload)

    base64_payload = (
        base64.b64encode(
            payload_string.encode()
        ).decode()
    )

    checksum_string = (
            base64_payload +
            endpoint +
            settings.PHONEPE_SALT_KEY
    )

    checksum = hashlib.sha256(
        checksum_string.encode()
    ).hexdigest()

    checksum = (
            checksum +
            "###" +
            settings.PHONEPE_SALT_INDEX
    )

    headers = {

        "Content-Type":
            "application/json",

        "X-VERIFY":
            checksum
    }

    url = (
        "https://api-preprod.phonepe.com"
        "/apis/pg-sandbox"
        "/pg/v1/pay"
    )

    response = requests.post(

        url,

        headers=headers,

        json={
            "request":
                base64_payload
        }
    )

    response_data = response.json()

    try:

        payment_url = (
            response_data['data']
            ['instrumentResponse']
            ['redirectInfo']['url']
        )

        return redirect(payment_url)

    except:

        subscription.payment_status = 'FAILED'

        subscription.save()

        return redirect('payment_failed')


# PAYMENT CALLBACK

@login_required
def payment_callback(request):
    transaction_id = request.POST.get(
        'transactionId'
    )

    try:

        subscription = (
            UserSubscription.objects.get(
                transaction_id=transaction_id
            )
        )

        subscription.payment_status = 'SUCCESS'

        subscription.is_active = True

        subscription.save()

        return redirect('payment_success')

    except:

        return redirect('payment_failed')


# PAYMENT SUCCESS PAGE

@login_required
def payment_success(request):
    return render(
        request,
        'subscriptions/payment_success.html'
    )


# PAYMENT FAILED PAGE

@login_required
def payment_failed(request):
    return render(
        request,
        'subscriptions/payment_failed.html'
    )


# USER PROFILE PAGE

@login_required
def profile(request):
    subscription = (

        UserSubscription.objects.filter(

            user=request.user,

            is_active=True,

            payment_status='SUCCESS'

        ).filter(

            Q(end_date__gte=timezone.now()) |

            Q(end_date__isnull=True)

        ).last()

    )

    context = {

        'subscription': subscription

    }

    return render(

        request,

        'subscriptions/profile.html',

        context
    )


# MY SUBSCRIPTION PAGE

@login_required
def my_subscription(request):
    subscriptions = (

        UserSubscription.objects.filter(

            user=request.user

        ).order_by('-created_at')

    )

    context = {

        'subscriptions': subscriptions

    }

    return render(

        request,

        'subscriptions/my_subscription.html',

        context
    )


# EPAPER PAGE

@login_required
def epaper(request):
    active_subscription = (

        UserSubscription.objects.filter(

            user=request.user,

            is_active=True,

            payment_status='SUCCESS'

        ).filter(

            Q(end_date__gte=timezone.now()) |

            Q(end_date__isnull=True)

        ).exists()

    )

    if not active_subscription:
        return redirect('plans')

    papers = (

        EPaper.objects.all()

        .order_by('-published_date')

    )

    context = {

        'papers': papers

    }

    return render(

        request,

        'subscriptions/epaper.html',

        context
    )
