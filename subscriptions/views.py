import uuid
import json
import base64
import hashlib
import hmac
import requests

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse
)
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib.auth.decorators import (
    login_required
)
from django.contrib import messages

from django.urls import reverse

from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt

from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from account.models import State, User
from account.views import (
    generate_strong_password,
    send_account_created_email
)

from .models import (
    Invoice,
    SubscriptionPlan,
    UserSubscription,
    EPaper
)

merchant_id = settings.PHONEPE_MERCHANT_ID
RAZORPAY_ORDERS_URL = 'https://api.razorpay.com/v1/orders'


def unique_subscriptions_by_plan(subscriptions):
    unique_subscriptions = []
    seen_plan_ids = set()

    for subscription in subscriptions:
        if subscription.plan_id in seen_plan_ids:
            continue

        unique_subscriptions.append(subscription)
        seen_plan_ids.add(subscription.plan_id)

    return unique_subscriptions


# SUBSCRIPTION PLANS PAGE


def plans(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('subscription_type','price')

    context = {
        'plans': plans
    }

    return render(
        request,
        'subscriptions/plans.html',
        context
    )


# SUBSCRIBE PAGE

def get_reporter_options():
    reporters = (
        User.objects
        .filter(user_type='reporter')
        .order_by('full_name', 'username', 'mobile')
    )
    reporter_options = []

    for reporter in reporters:
        mobile = (reporter.mobile or '').strip()

        if not mobile:
            continue

        reporter_options.append({
            'mobile': mobile,
            'name': (
                reporter.full_name or
                reporter.username or
                reporter.email or
                mobile
            ),
        })

    return reporter_options


def get_subscribe_context(request, plan, **extra_context):
    subscription_customer = None
    subscription_customer_id = request.session.get('subscription_customer_id')

    if subscription_customer_id:
        subscription_customer = (
            User.objects
            .filter(id=subscription_customer_id, user_type='subscriber')
            .first()
        )

    is_reporter = (
        request.user.is_authenticated and
        request.user.user_type == 'reporter'
    )

    context = {
        'plan': plan,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'account_states': State.objects.filter(country__code='IN'),
        'default_state': 'Uttar Pradesh',
        'reporter_mobile': request.session.get('reporter_mobile', ''),
        'reporter_options': get_reporter_options(),
        'subscription_customer': subscription_customer,
        'can_start_payment': (
            request.user.is_authenticated or
            bool(subscription_customer)
        ),
        'show_account_form': (
            (
                not request.user.is_authenticated or
                is_reporter
            ) and
            not subscription_customer
        ),
    }
    context.update(extra_context)
    return context


def is_reporter_mobile_allowed(reporter_mobile):
    if not reporter_mobile:
        return True

    return User.objects.filter(
        user_type='reporter',
        mobile=reporter_mobile
    ).exists()


def create_reporter_account(request):
    if request.method != 'POST':
        return JsonResponse(
            {
                'error': 'Invalid request method.'
            },
            status=405
        )

    first_name = (request.POST.get('first_name') or '').strip()
    last_name = (request.POST.get('last_name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    mobile = (request.POST.get('mobile') or '').strip()
    address = (request.POST.get('address') or '').strip()
    city = (request.POST.get('city') or '').strip()
    pincode = (request.POST.get('pincode') or '').strip()
    state = (request.POST.get('state') or 'Uttar Pradesh').strip()
    country = (request.POST.get('country') or 'India').strip()

    if not first_name or not last_name or not email or not mobile:
        return JsonResponse(
            {
                'error': 'First name, last name, email and mobile are required.'
            },
            status=400
        )

    if User.objects.filter(email=email).exists():
        return JsonResponse(
            {
                'error': 'Email already exists.'
            },
            status=400
        )

    if User.objects.filter(mobile=mobile).exists():
        return JsonResponse(
            {
                'error': 'Mobile already exists.'
            },
            status=400
        )

    full_name = f'{first_name} {last_name}'.strip()
    password = generate_strong_password()
    user = User.objects.create_user(
        username=email,
        email=email,
        mobile=mobile,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        address=address,
        city=city,
        state=state,
        pincode=pincode,
        country=country,
        user_type='reporter',
        password=password
    )
    send_account_created_email(user, password)

    return JsonResponse(
        {
            'message': 'Reporter account created successfully.',
            'reporter': {
                'name': full_name or user.username,
                'mobile': mobile,
            }
        }
    )


def subscribe(request, plan_id):
    plan = get_object_or_404(
        SubscriptionPlan,
        id=plan_id,
        is_active=True
    )

    if request.user.is_authenticated and (
        request.user.is_staff or request.user.is_superuser
    ):
        messages.error(
            request,
            'Admin users cannot purchase subscriptions. Please use a normal user account.'
        )
        return redirect('profile')

    if (
        request.method == 'POST' and
        (
            not request.user.is_authenticated or
            request.user.user_type == 'reporter'
        )
    ):
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        reporter_mobile = (request.POST.get('reporter_mobile') or '').strip()

        if not is_reporter_mobile_allowed(reporter_mobile):
            messages.error(
                request,
                'Please select a valid reporter from the list.'
            )
            return render(
                request,
                'subscriptions/subscribe.html',
                get_subscribe_context(
                    request,
                    plan,
                    register_error='Please select a valid reporter from the list.',
                )
            )

        if User.objects.filter(email=email).exists():
            messages.error(
                request,
                'Email already exists. Please login with your existing account.'
            )
            return render(
                request,
                'subscriptions/subscribe.html',
                get_subscribe_context(
                    request,
                    plan,
                    register_error='Email already exists. Please login with your existing account.',
                )
            )

        if mobile and User.objects.filter(mobile=mobile).exists():
            messages.error(
                request,
                'Mobile already exists. Please login with your existing account.'
            )
            return render(
                request,
                'subscriptions/subscribe.html',
                get_subscribe_context(
                    request,
                    plan,
                    register_error='Mobile already exists. Please login with your existing account.',
                )
            )

        password = generate_strong_password()
        full_name = (request.POST.get('full_name') or '').strip()
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        user = User.objects.create_user(
            username=email or mobile,
            email=email,
            mobile=mobile,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            user_type='subscriber',
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state') or 'Uttar Pradesh',
            pincode=request.POST.get('pincode'),
            country=request.POST.get('country') or 'India',
            password=password
        )
        send_account_created_email(user, password)

        request.session['subscription_customer_id'] = user.id
        request.session['reporter_mobile'] = reporter_mobile
        messages.success(
            request,
            'Account created successfully. Login details have been sent to your email.'
        )

    return render(
        request,
        'subscriptions/subscribe.html',
        get_subscribe_context(request, plan)
    )


def get_payment_user(request):
    subscription_customer_id = request.session.get('subscription_customer_id')

    if subscription_customer_id:
        customer = (
            User.objects
            .filter(id=subscription_customer_id, user_type='subscriber')
            .first()
        )

        if customer:
            return customer

    return request.user


def clear_subscription_customer_session(request, user_id=None):
    subscription_customer_id = request.session.get('subscription_customer_id')

    if not subscription_customer_id:
        return

    if user_id is not None and str(subscription_customer_id) != str(user_id):
        return

    request.session.pop('subscription_customer_id', None)
    request.session.pop('reporter_mobile', None)


def checkout_has_payment_user(request):
    if request.user.is_authenticated:
        return True

    subscription_customer_id = request.session.get('subscription_customer_id')

    if not subscription_customer_id:
        return False

    return User.objects.filter(
        id=subscription_customer_id,
        user_type='subscriber'
    ).exists()


def verify_razorpay_signature(message, signature, secret):
    if not signature or not secret:
        return False

    expected_signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def mark_subscription_success(subscription):
    was_success = subscription.payment_status == 'SUCCESS'
    subscription.payment_status = 'SUCCESS'
    subscription.is_active = True
    subscription.save()

    if subscription.user.user_type != 'subscriber':
        subscription.user.user_type = 'subscriber'
        subscription.user.save(update_fields=['user_type'])

    invoice = get_or_create_invoice(subscription)

    if not was_success:
        send_subscription_success_email(subscription, invoice)

    (
        UserSubscription.objects
        .filter(
            user=subscription.user,
            plan=subscription.plan,
            payment_status='PENDING'
        )
        .exclude(id=subscription.id)
        .update(payment_status='FAILED', is_active=False)
    )


def mark_subscription_failed(subscription):
    subscription.payment_status = 'FAILED'
    subscription.is_active = False
    subscription.save()


def get_or_create_invoice(subscription):
    user = subscription.user
    invoice_number = f'GT-{timezone.now().strftime("%Y%m%d")}-{subscription.id:06d}'
    billing_defaults = {
        'invoice_number': invoice_number,
        'billing_name': (
            user.full_name or
            user.get_full_name() or
            user.username
        ),
        'billing_email': user.email or '',
        'billing_mobile': user.mobile or '',
        'billing_address': user.address or '',
        'billing_city': user.city or '',
        'billing_state': user.state or '',
        'billing_pincode': user.pincode or '',
        'billing_country': user.country or 'India',
        'amount': subscription.amount,
    }

    invoice, _ = Invoice.objects.get_or_create(
        subscription=subscription,
        defaults=billing_defaults
    )

    invoice_fields = [
        'billing_name',
        'billing_email',
        'billing_mobile',
        'billing_address',
        'billing_city',
        'billing_state',
        'billing_pincode',
        'billing_country',
        'amount',
    ]
    changed_fields = []

    for field in invoice_fields:
        value = billing_defaults[field]

        if getattr(invoice, field) != value:
            setattr(invoice, field, value)
            changed_fields.append(field)

    if changed_fields:
        invoice.save(update_fields=changed_fields)

    return invoice


def send_subscription_success_email(subscription, invoice):
    user = subscription.user

    if not user.email:
        return

    context = {
        'user': user,
        'subscription': subscription,
        'invoice': invoice,
        'login_url': f'{settings.BASE_URL}/login/',
        'site_url': settings.BASE_URL,
    }
    subject = f'Subscription active - Invoice {invoice.invoice_number}'
    text_body = render_to_string(
        'emails/subscription_success.txt',
        context
    )
    html_body = render_to_string(
        'emails/subscription_success.html',
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


def send_delivery_status_email(invoice):
    user = invoice.subscription.user

    if not user.email:
        return

    context = {
        'user': user,
        'invoice': invoice,
        'subscription': invoice.subscription,
        'login_url': f'{settings.BASE_URL}/login/',
        'site_url': settings.BASE_URL,
    }
    subject = f'Delivery update - {invoice.invoice_number}'
    text_body = render_to_string(
        'emails/delivery_status.txt',
        context
    )
    html_body = render_to_string(
        'emails/delivery_status.html',
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


def send_account_updated_email(user):
    if not user.email:
        return

    context = {
        'user': user,
        'login_url': f'{settings.BASE_URL}/login/',
        'site_url': settings.BASE_URL,
    }
    subject = 'Your Gargachary Times account details were updated'
    text_body = render_to_string(
        'emails/account_updated.txt',
        context
    )
    html_body = render_to_string(
        'emails/account_updated.html',
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


def razorpay_create_order(request, plan_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    if not checkout_has_payment_user(request):
        return JsonResponse(
            {
                'error': 'Please create the subscriber account before starting payment.'
            },
            status=403
        )

    if (
        request.user.is_authenticated and
        (request.user.is_staff or request.user.is_superuser)
    ):
        return JsonResponse(
            {
                'error': 'Admin users cannot purchase subscriptions. Please use a normal user account.'
            },
            status=403
        )

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return JsonResponse(
            {
                'error': 'Razorpay keys are not configured.'
            },
            status=500
        )

    plan = get_object_or_404(
        SubscriptionPlan,
        id=plan_id,
        is_active=True
    )
    payment_user = get_payment_user(request)
    reporter_mobile = (request.POST.get('reporter_mobile') or '').strip()

    if not is_reporter_mobile_allowed(reporter_mobile):
        return JsonResponse(
            {
                'error': 'Please select a valid reporter from the list.'
            },
            status=400
        )

    active_subscription_exists = (
        UserSubscription.objects
        .filter(
            user=payment_user,
            plan=plan,
            is_active=True,
            payment_status='SUCCESS'
        )
        .filter(
            Q(end_date__gte=timezone.now()) |
            Q(end_date__isnull=True)
        )
        .exists()
    )

    if active_subscription_exists:
        return JsonResponse(
            {
                'error': 'This subscription plan is already active on your account.'
            },
            status=409
        )

    pending_subscription = (
        UserSubscription.objects
        .filter(
            user=payment_user,
            plan=plan,
            payment_status='PENDING',
            transaction_id__startswith='order_'
        )
        .order_by('-created_at')
        .first()
    )

    if pending_subscription:
        if pending_subscription.reporter_mobile != reporter_mobile:
            pending_subscription.reporter_mobile = reporter_mobile
            pending_subscription.save(update_fields=['reporter_mobile'])

        clear_subscription_customer_session(
            request,
            pending_subscription.user_id
        )

        return JsonResponse(
            {
                'key': settings.RAZORPAY_KEY_ID,
                'order_id': pending_subscription.transaction_id,
                'payment_link': request.build_absolute_uri(
                    reverse(
                        'razorpay_shared_payment',
                        args=[pending_subscription.transaction_id]
                    )
                ),
                'amount': int(pending_subscription.amount * 100),
                'currency': 'INR',
                'name': 'Gargachary Times',
                'description': plan.name,
                'prefill': {
                    'name': payment_user.full_name or payment_user.username,
                    'email': payment_user.email,
                    'contact': getattr(payment_user, 'mobile', '') or '',
                },
                'callback_url': request.build_absolute_uri(
                    reverse('razorpay_payment_callback')
                ),
            }
        )

    receipt = f"sub_{payment_user.id}_{uuid.uuid4().hex[:24]}"

    payload = {
        'amount': int(plan.price * 100),
        'currency': 'INR',
        'receipt': receipt,
        'payment_capture': 1,
        'notes': {
            'user_id': str(payment_user.id),
            'created_by_user_id': (
                str(request.user.id)
                if request.user.is_authenticated
                else ''
            ),
            'subscription_user_id': str(payment_user.id),
            'plan_id': str(plan.id),
            'plan_name': plan.name,
        }
    }

    response = requests.post(
        RAZORPAY_ORDERS_URL,
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ),
        json=payload,
        timeout=15
    )

    if response.status_code >= 400:
        return JsonResponse(
            {
                'error': 'Unable to create Razorpay order.'
            },
            status=502
        )

    order = response.json()

    subscription = UserSubscription.objects.create(
        user=payment_user,
        plan=plan,
        amount=plan.price,
        transaction_id=order['id'],
        reporter_mobile=reporter_mobile,
        payment_status='PENDING'
    )
    clear_subscription_customer_session(request, subscription.user_id)

    return JsonResponse(
        {
            'key': settings.RAZORPAY_KEY_ID,
            'order_id': order['id'],
            'payment_link': request.build_absolute_uri(
                reverse(
                    'razorpay_shared_payment',
                    args=[order['id']]
                )
            ),
            'amount': order['amount'],
            'currency': order['currency'],
            'name': 'Gargachary Times',
            'description': plan.name,
            'prefill': {
                'name': payment_user.full_name or payment_user.get_full_name() or payment_user.username,
                'email': payment_user.email,
                'contact': getattr(payment_user, 'mobile', '') or '',
            },
            'callback_url': request.build_absolute_uri(
                reverse('razorpay_payment_callback')
            ),
        }
    )


def razorpay_shared_payment(request, order_id):
    subscription = get_object_or_404(
        UserSubscription,
        transaction_id=order_id
    )

    if subscription.payment_status == 'SUCCESS':
        return render(
            request,
            'subscriptions/payment_success.html'
        )

    if subscription.payment_status == 'FAILED':
        return render(
            request,
            'subscriptions/payment_failed.html'
        )

    context = {
        'subscription': subscription,
        'plan': subscription.plan,
        'key': settings.RAZORPAY_KEY_ID,
        'order_id': subscription.transaction_id,
        'amount': int(subscription.amount * 100),
        'currency': 'INR',
        'name': 'Gargachary Times',
        'description': subscription.plan.name,
        'prefill': {
            'name': subscription.user.full_name or subscription.user.username,
            'email': subscription.user.email,
            'contact': getattr(subscription.user, 'mobile', '') or '',
        },
        'callback_url': request.build_absolute_uri(
            reverse('razorpay_payment_callback')
        ),
    }

    return render(
        request,
        'subscriptions/shared_payment.html',
        context
    )


def razorpay_payment_callback(request):
    if request.method != 'POST':
        return render(
            request,
            'subscriptions/payment_failed.html'
        )

    payment_id = request.POST.get('razorpay_payment_id')
    order_id = request.POST.get('razorpay_order_id')
    signature = request.POST.get('razorpay_signature')

    if not payment_id or not order_id or not signature:
        return render(
            request,
            'subscriptions/payment_failed.html'
        )

    try:
        subscription = UserSubscription.objects.get(
            transaction_id=order_id
        )
    except UserSubscription.DoesNotExist:
        return render(
            request,
            'subscriptions/payment_failed.html'
        )

    message = f'{order_id}|{payment_id}'
    if verify_razorpay_signature(
        message,
        signature,
        settings.RAZORPAY_KEY_SECRET
    ):
        mark_subscription_success(subscription)
        clear_subscription_customer_session(request, subscription.user_id)
        return render(
            request,
            'subscriptions/payment_success.html'
        )

    mark_subscription_failed(subscription)
    return render(
        request,
        'subscriptions/payment_failed.html'
    )


@csrf_exempt
def razorpay_webhook(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return HttpResponseBadRequest('Webhook secret is not configured')

    payload = request.body.decode('utf-8')
    signature = request.headers.get('X-Razorpay-Signature')

    if not verify_razorpay_signature(
        payload,
        signature,
        settings.RAZORPAY_WEBHOOK_SECRET
    ):
        return HttpResponseBadRequest('Invalid signature')

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid payload')

    event_name = event.get('event')
    payment = (
        event.get('payload', {})
        .get('payment', {})
        .get('entity', {})
    )
    order_id = payment.get('order_id')
    payment_id = payment.get('id')

    if event_name in ('payment.captured', 'order.paid') and order_id:
        subscription = (
            UserSubscription.objects
            .filter(transaction_id=order_id)
            .first()
        )

        if subscription:
            mark_subscription_success(subscription)

    elif event_name == 'payment.failed' and order_id:
        subscription = (
            UserSubscription.objects
            .filter(transaction_id=order_id)
            .first()
        )

        if subscription:
            mark_subscription_failed(subscription)

    return HttpResponse(status=200)


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


@login_required
def invoice_detail(request, invoice_number):
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'subscription',
            'subscription__plan',
            'subscription__user'
        ),
        invoice_number=invoice_number,
        subscription__user=request.user
    )

    return render(
        request,
        'subscriptions/invoice.html',
        {
            'invoice': invoice
        }
    )


# USER PROFILE PAGE

@login_required
def profile(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')

        if (
            email and
            User.objects.exclude(id=request.user.id).filter(email=email).exists()
        ):
            messages.error(request, 'Email already exists.')
            return redirect('profile')

        if (
            mobile and
            User.objects.exclude(id=request.user.id).filter(mobile=mobile).exists()
        ):
            messages.error(request, 'Mobile already exists.')
            return redirect('profile')

        request.user.full_name = request.POST.get('full_name')
        request.user.email = email
        request.user.mobile = mobile
        request.user.address = request.POST.get('address')
        request.user.city = request.POST.get('city')
        request.user.state = request.POST.get('state')
        request.user.pincode = request.POST.get('pincode')
        request.user.country = request.POST.get('country') or 'India'
        request.user.save()

        send_account_updated_email(request.user)
        messages.success(request, 'Account details updated successfully.')
        return redirect('profile')

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

    subscriptions = (
        UserSubscription.objects
        .select_related('plan', 'invoice')
        .filter(user=request.user)
        .order_by('-created_at')
    )
    subscriptions = unique_subscriptions_by_plan(subscriptions)

    context = {

        'subscription': subscription,
        'subscriptions': subscriptions,
        'account_states': State.objects.filter(country__code='IN'),
        'default_state': request.user.state or 'Uttar Pradesh',

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

        ).select_related('plan', 'invoice').order_by('-created_at')

    )
    subscriptions = unique_subscriptions_by_plan(subscriptions)

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
