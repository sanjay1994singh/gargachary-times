import uuid
import json
import base64
import hashlib
import hmac
import requests
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

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

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from account.models import State, User
from account.views import (
    generate_strong_password,
    send_account_created_email
)

from .models import (
    PaymentWebhookLog,
    DisputeEvidence,
    Invoice,
    RefundRecord,
    SubscriptionPlan,
    UserSubscription
)

merchant_id = settings.PHONEPE_MERCHANT_ID
RAZORPAY_ORDERS_URL = 'https://api.razorpay.com/v1/orders'
RAZORPAY_PAYMENTS_URL = 'https://api.razorpay.com/v1/payments/{payment_id}'


def unique_subscriptions_by_plan(subscriptions):
    unique_subscriptions = []
    seen_plan_ids = set()

    for subscription in subscriptions:
        if subscription.plan_id in seen_plan_ids:
            continue

        unique_subscriptions.append(subscription)
        seen_plan_ids.add(subscription.plan_id)

    return unique_subscriptions


def ensure_paid_subscription_invoices(subscriptions):
    for subscription in subscriptions:
        if subscription.payment_status not in ('SUCCESS', 'CAPTURED'):
            continue

        try:
            subscription.invoice
        except ObjectDoesNotExist:
            subscription.invoice = get_or_create_invoice(subscription)

    return subscriptions


def calculate_inclusive_gst(total_amount, gst_rate=Decimal('5.00')):
    total_amount = Decimal(total_amount or 0).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )
    divisor = Decimal('1.00') + (gst_rate / Decimal('100'))
    taxable_amount = (total_amount / divisor).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )
    tax_amount = (total_amount - taxable_amount).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )

    return {
        'gst_rate': gst_rate.quantize(Decimal('0.01')),
        'taxable_amount': taxable_amount,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
    }


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
    subscription_customer_plan_id = request.session.get(
        'subscription_customer_plan_id'
    )

    if (
        subscription_customer_id and
        str(subscription_customer_plan_id) == str(plan.id)
    ):
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


def create_pending_subscription_record(user, plan, reporter_mobile=''):
    subscription, created = UserSubscription.objects.get_or_create(
        user=user,
        plan=plan,
        payment_status='PENDING',
        defaults={
            'amount': plan.price,
            'transaction_id': f'pending_{user.id}_{plan.id}',
            'reporter_mobile': reporter_mobile,
        }
    )

    update_fields = []
    if subscription.amount != plan.price:
        subscription.amount = plan.price
        update_fields.append('amount')

    if reporter_mobile and subscription.reporter_mobile != reporter_mobile:
        subscription.reporter_mobile = reporter_mobile
        update_fields.append('reporter_mobile')

    if update_fields:
        subscription.save(update_fields=update_fields)

    return subscription


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
    email = (request.POST.get('email') or '').strip().lower()
    mobile = (request.POST.get('mobile') or '').strip()
    address = (request.POST.get('address') or '').strip()
    city = (request.POST.get('city') or '').strip()
    district = (request.POST.get('district') or '').strip()
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

    if User.objects.filter(mobile=mobile).exists():
        return JsonResponse(
            {
                'error': 'Mobile already exists.'
            },
            status=400
        )

    full_name = f'{first_name} {last_name}'.strip()
    password = generate_strong_password()
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=mobile,
                email=email,
                mobile=mobile,
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                address=address,
                city=city,
                district=district,
                state=state,
                pincode=pincode,
                country=country,
                user_type='reporter',
                password=password
            )
        send_account_created_email(user, password)
    except IntegrityError:
        return JsonResponse(
            {
                'error': 'This email or mobile number is already registered.'
            },
            status=400
        )

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

    if request.GET.get('new') == '1':
        clear_subscription_customer_session(request)

    clear_stale_subscription_customer_session(request, plan)

    if (
        request.method == 'POST' and
        (
            not request.user.is_authenticated or
            request.user.user_type == 'reporter'
        )
    ):
        email = (request.POST.get('email') or '').strip().lower() or None
        mobile = (request.POST.get('mobile') or '').strip()
        full_name = (request.POST.get('full_name') or '').strip()
        address = (request.POST.get('address') or '').strip()
        city = (request.POST.get('city') or '').strip()
        district = (request.POST.get('district') or '').strip()
        pincode = (request.POST.get('pincode') or '').strip()
        state = (request.POST.get('state') or 'Uttar Pradesh').strip()
        country = (request.POST.get('country') or 'India').strip()
        reporter_mobile = (request.POST.get('reporter_mobile') or '').strip()

        if not all([
            full_name,
            mobile,
            city,
            district,
            address,
            pincode,
            state,
            country,
        ]):
            messages.error(
                request,
                'Full name, mobile, city, district, address, PIN code, state and country are required.'
            )
            return render(
                request,
                'subscriptions/subscribe.html',
                get_subscribe_context(
                    request,
                    plan,
                    register_error='Full name, mobile, city, district, address, PIN code, state and country are required.',
                )
            )

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
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        try:
            with transaction.atomic():
                user = User(
                    username=mobile,
                    email=email,
                    mobile=mobile,
                    first_name=first_name,
                    last_name=last_name,
                    full_name=full_name,
                    user_type='subscriber',
                    address=address,
                    city=city,
                    district=district,
                    state=state,
                    pincode=pincode,
                    country=country,
                )
                user.set_password(password)
                user.save()
                create_pending_subscription_record(user, plan, reporter_mobile)
        except IntegrityError:
            messages.error(
                request,
                'This email or mobile number is already registered. Please login with your existing account.'
            )
            return render(
                request,
                'subscriptions/subscribe.html',
                get_subscribe_context(
                    request,
                    plan,
                    register_error='This email or mobile number is already registered. Please login with your existing account.',
                )
            )

        send_account_created_email(user, password)

        request.session['subscription_customer_id'] = user.id
        request.session['subscription_customer_plan_id'] = plan.id
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
    request.session.pop('subscription_customer_plan_id', None)
    request.session.pop('reporter_mobile', None)


def clear_stale_subscription_customer_session(request, plan):
    subscription_customer_id = request.session.get('subscription_customer_id')
    subscription_customer_plan_id = request.session.get(
        'subscription_customer_plan_id'
    )

    if not subscription_customer_id:
        return

    if str(subscription_customer_plan_id) == str(plan.id):
        return

    clear_subscription_customer_session(request)


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


def get_razorpay_datetime(timestamp):
    if not timestamp:
        return None

    return datetime.fromtimestamp(
        int(timestamp),
        tz=timezone.get_current_timezone()
    )


def update_subscription_payment_details(
    subscription,
    payment_id='',
    signature='',
    payment_entity=None
):
    payment_entity = payment_entity or {}
    update_fields = []

    field_values = {
        'razorpay_order_id': payment_entity.get('order_id') or subscription.transaction_id,
        'razorpay_payment_id': payment_id or payment_entity.get('id') or '',
        'razorpay_signature': signature or subscription.razorpay_signature,
        'payment_method': payment_entity.get('method') or subscription.payment_method,
        'currency': payment_entity.get('currency') or subscription.currency or 'INR',
    }

    created_at = get_razorpay_datetime(payment_entity.get('created_at'))

    if created_at:
        field_values['paid_at'] = created_at

    if payment_entity.get('captured') or payment_entity.get('status') == 'captured':
        field_values['captured_at'] = created_at or timezone.now()
        field_values['payment_status'] = 'CAPTURED'

    elif payment_entity.get('status') == 'authorized':
        field_values['payment_status'] = 'AUTHORIZED'

    if payment_entity:
        field_values['gateway_response'] = payment_entity

    for field, value in field_values.items():
        if value and getattr(subscription, field) != value:
            setattr(subscription, field, value)
            update_fields.append(field)

    if update_fields:
        subscription.save(update_fields=update_fields)


def fetch_razorpay_payment(payment_id):
    if not payment_id:
        return {}

    response = requests.get(
        RAZORPAY_PAYMENTS_URL.format(payment_id=payment_id),
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ),
        timeout=10
    )

    if response.status_code >= 400:
        return {}

    return response.json()


def mark_subscription_success(
    subscription,
    payment_id='',
    signature='',
    payment_entity=None
):
    was_success = subscription.payment_status == 'SUCCESS'
    update_subscription_payment_details(
        subscription,
        payment_id=payment_id,
        signature=signature,
        payment_entity=payment_entity
    )
    subscription.payment_status = 'SUCCESS'
    subscription.is_active = True
    subscription.access_status = 'ACTIVE'
    if not subscription.paid_at:
        subscription.paid_at = timezone.now()
    if not subscription.captured_at:
        subscription.captured_at = subscription.paid_at
    if not subscription.activated_at:
        subscription.activated_at = timezone.now()
    if not subscription.delivered_at:
        subscription.delivered_at = subscription.activated_at
    subscription.save(
        update_fields=[
            'payment_status',
            'is_active',
            'access_status',
            'paid_at',
            'captured_at',
            'activated_at',
            'delivered_at',
            'updated_at',
        ]
    )

    if subscription.user.user_type != 'subscriber':
        subscription.user.user_type = 'subscriber'
        subscription.user.save(update_fields=['user_type'])

    invoice = get_or_create_invoice(subscription)
    invoice_fields = []

    if not invoice.service_confirmed_at:
        invoice.service_confirmed_at = timezone.now()
        invoice.delivery_status = 'DELIVERED'
        invoice.delivery_note = (
            invoice.delivery_note or
            'Subscription access activated after successful Razorpay payment.'
        )
        invoice_fields.extend([
            'service_confirmed_at',
            'delivery_status',
            'delivery_note',
        ])

    if not was_success:
        send_subscription_success_email(subscription, invoice)
        invoice.customer_notified_at = timezone.now()
        invoice_fields.append('customer_notified_at')

    if invoice_fields:
        invoice_fields = list(dict.fromkeys(invoice_fields + ['updated_at']))
        invoice.save(update_fields=invoice_fields)

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
    subscription.access_status = 'PENDING'
    subscription.save(
        update_fields=[
            'payment_status',
            'is_active',
            'access_status',
            'updated_at',
        ]
    )


def get_or_create_invoice(subscription):
    user = subscription.user
    invoice_number = f'GT-{timezone.now().strftime("%Y%m%d")}-{subscription.id:06d}'
    gst_breakup = calculate_inclusive_gst(subscription.amount)
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
        'tax_amount': gst_breakup['tax_amount'],
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
        'tax_amount',
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
        'refund_policy_url': f'{settings.BASE_URL}/refund-policy/',
        'terms_url': f'{settings.BASE_URL}/terms-and-conditions/',
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
            payment_status='PENDING'
        )
        .order_by('-created_at')
        .first()
    )

    if (
        pending_subscription and
        pending_subscription.transaction_id.startswith('order_')
    ):
        update_fields = []

        if pending_subscription.reporter_mobile != reporter_mobile:
            pending_subscription.reporter_mobile = reporter_mobile
            update_fields.append('reporter_mobile')

        if not pending_subscription.razorpay_order_id:
            pending_subscription.razorpay_order_id = (
                pending_subscription.transaction_id
            )
            update_fields.append('razorpay_order_id')

        if update_fields:
            update_fields.append('updated_at')
            pending_subscription.save(update_fields=update_fields)

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

    if pending_subscription:
        subscription = pending_subscription
        subscription.amount = plan.price
        subscription.transaction_id = order['id']
        subscription.razorpay_order_id = order['id']
        subscription.razorpay_receipt = order.get('receipt') or receipt
        subscription.currency = order.get('currency') or 'INR'
        subscription.gateway_response = order
        subscription.reporter_mobile = reporter_mobile
        subscription.save(
            update_fields=[
                'amount',
                'transaction_id',
                'razorpay_order_id',
                'razorpay_receipt',
                'currency',
                'gateway_response',
                'reporter_mobile',
                'updated_at',
            ]
        )
    else:
        subscription = UserSubscription.objects.create(
            user=payment_user,
            plan=plan,
            amount=plan.price,
            transaction_id=order['id'],
            razorpay_order_id=order['id'],
            razorpay_receipt=order.get('receipt') or receipt,
            currency=order.get('currency') or 'INR',
            gateway_response=order,
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


def create_razorpay_subscription_order(request, subscriber, plan, reporter_mobile=''):
    pending_subscription = (
        UserSubscription.objects
        .filter(
            user=subscriber,
            plan=plan,
            payment_status='PENDING'
        )
        .order_by('-created_at')
        .first()
    )

    if (
        pending_subscription and
        pending_subscription.transaction_id.startswith('order_')
    ):
        update_fields = []

        if pending_subscription.reporter_mobile != reporter_mobile:
            pending_subscription.reporter_mobile = reporter_mobile
            update_fields.append('reporter_mobile')

        if not pending_subscription.razorpay_order_id:
            pending_subscription.razorpay_order_id = (
                pending_subscription.transaction_id
            )
            update_fields.append('razorpay_order_id')

        if update_fields:
            update_fields.append('updated_at')
            pending_subscription.save(update_fields=update_fields)

        return pending_subscription

    receipt = f"sub_{subscriber.id}_{uuid.uuid4().hex[:24]}"
    payload = {
        'amount': int(plan.price * 100),
        'currency': 'INR',
        'receipt': receipt,
        'payment_capture': 1,
        'notes': {
            'user_id': str(subscriber.id),
            'created_by_user_id': str(request.user.id),
            'subscription_user_id': str(subscriber.id),
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
        raise requests.RequestException('Unable to create Razorpay order.')

    order = response.json()

    if pending_subscription:
        pending_subscription.amount = plan.price
        pending_subscription.transaction_id = order['id']
        pending_subscription.razorpay_order_id = order['id']
        pending_subscription.razorpay_receipt = order.get('receipt') or receipt
        pending_subscription.currency = order.get('currency') or 'INR'
        pending_subscription.gateway_response = order
        pending_subscription.reporter_mobile = reporter_mobile
        pending_subscription.save(
            update_fields=[
                'amount',
                'transaction_id',
                'razorpay_order_id',
                'razorpay_receipt',
                'currency',
                'gateway_response',
                'reporter_mobile',
                'updated_at',
            ]
        )
        return pending_subscription

    return UserSubscription.objects.create(
        user=subscriber,
        plan=plan,
        amount=plan.price,
        transaction_id=order['id'],
        razorpay_order_id=order['id'],
        razorpay_receipt=order.get('receipt') or receipt,
        currency=order.get('currency') or 'INR',
        gateway_response=order,
        reporter_mobile=reporter_mobile,
        payment_status='PENDING'
    )


def is_reporter_user(user):
    return (
        user.is_authenticated and
        user.user_type == 'reporter'
    )


def get_mobile_last10(value):
    digits = ''.join(
        char
        for char in (value or '')
        if char.isdigit()
    )

    if len(digits) >= 10:
        return digits[-10:]

    return digits


@login_required
def reporter_unpaid_subscribers(request):
    if not is_reporter_user(request.user):
        messages.error(
            request,
            'Only reporter accounts can view unpaid subscribers.'
        )
        return redirect('profile')

    reporter_mobile = get_mobile_last10(request.user.mobile)

    if not reporter_mobile:
        messages.error(
            request,
            'Reporter mobile number is missing on your account.'
        )
        return redirect('profile')

    reporter_subscriptions = (
        UserSubscription.objects
        .select_related('user', 'plan')
        .exclude(payment_status='SUCCESS')
        .exclude(reporter_mobile='')
        .order_by('-created_at')
    )
    subscribers = []
    seen_user_ids = set()

    for subscription in reporter_subscriptions:
        if get_mobile_last10(subscription.reporter_mobile) != reporter_mobile:
            continue

        if subscription.user_id in seen_user_ids:
            continue

        subscription.user.latest_reporter_subscription = subscription
        subscribers.append(subscription.user)
        seen_user_ids.add(subscription.user_id)

    return render(
        request,
        'subscriptions/reporter_unpaid_subscribers.html',
        {
            'active_menu': 'reporter_subscribers',
            'page_title': 'Unpaid Subscribers',
            'subscribers': subscribers,
            'empty_message': 'No unpaid subscriber records found.',
        }
    )


@login_required
def reporter_success_subscribers(request):
    if not is_reporter_user(request.user):
        messages.error(
            request,
            'Only reporter accounts can view successful subscribers.'
        )
        return redirect('profile')

    reporter_mobile = get_mobile_last10(request.user.mobile)

    if not reporter_mobile:
        messages.error(
            request,
            'Reporter mobile number is missing on your account.'
        )
        return redirect('profile')

    reporter_subscriptions = (
        UserSubscription.objects
        .select_related('user', 'plan')
        .filter(payment_status='SUCCESS')
        .exclude(reporter_mobile='')
        .order_by('-created_at')
    )
    subscribers = []
    seen_user_ids = set()

    for subscription in reporter_subscriptions:
        if get_mobile_last10(subscription.reporter_mobile) != reporter_mobile:
            continue

        if subscription.user_id in seen_user_ids:
            continue

        subscription.user.latest_reporter_subscription = subscription
        subscribers.append(subscription.user)
        seen_user_ids.add(subscription.user_id)

    return render(
        request,
        'subscriptions/reporter_unpaid_subscribers.html',
        {
            'active_menu': 'reporter_success_subscribers',
            'page_title': 'Success Subscribers',
            'subscribers': subscribers,
            'empty_message': 'No successful subscriber records found.',
        }
    )


@login_required
def reporter_unpaid_subscriber_detail(request, user_id):
    if not is_reporter_user(request.user):
        messages.error(
            request,
            'Only reporter accounts can view subscriber details.'
        )
        return redirect('profile')

    subscriber = get_object_or_404(
        User,
        id=user_id,
        user_type='subscriber'
    )
    reporter_mobile = get_mobile_last10(request.user.mobile)

    if not reporter_mobile:
        messages.error(
            request,
            'Reporter mobile number is missing on your account.'
        )
        return redirect('profile')

    reporter_link_exists = UserSubscription.objects.filter(
        user=subscriber,
        reporter_mobile__endswith=reporter_mobile
    ).exists()

    if not reporter_link_exists:
        messages.error(
            request,
            'This subscriber is not linked with your reporter account.'
        )
        return redirect('reporter_unpaid_subscribers')

    subscriptions = (
        UserSubscription.objects
        .select_related('plan', 'invoice')
        .filter(user=subscriber, reporter_mobile__endswith=reporter_mobile)
        .order_by('-created_at')
    )
    pending_subscriptions = subscriptions.filter(payment_status='PENDING')
    selected_subscription = pending_subscriptions.first() or subscriptions.first()
    selected_plan_id = (
        selected_subscription.plan_id
        if selected_subscription
        else None
    )
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by(
        'subscription_type',
        'price'
    )

    return render(
        request,
        'subscriptions/reporter_unpaid_subscriber_detail.html',
        {
            'active_menu': 'reporter_subscribers',
            'page_title': 'Subscriber Detail',
            'subscriber': subscriber,
            'subscriptions': subscriptions,
            'pending_subscriptions': pending_subscriptions,
            'plans': plans,
            'selected_plan_id': selected_plan_id,
        }
    )


@login_required
@require_POST
def reporter_generate_subscriber_payment(request, user_id):
    if not is_reporter_user(request.user):
        messages.error(
            request,
            'Only reporter accounts can generate subscriber payments.'
        )
        return redirect('profile')

    subscriber = get_object_or_404(
        User,
        id=user_id,
        user_type='subscriber'
    )
    reporter_mobile = get_mobile_last10(request.user.mobile)

    if not reporter_mobile:
        messages.error(
            request,
            'Reporter mobile number is missing on your account.'
        )
        return redirect('profile')

    if UserSubscription.objects.filter(
        user=subscriber,
        reporter_mobile__endswith=reporter_mobile
    ).exists() is False:
        messages.error(
            request,
            'This subscriber is not linked with your reporter account.'
        )
        return redirect('reporter_unpaid_subscribers')

    plan = get_object_or_404(
        SubscriptionPlan,
        id=request.POST.get('plan_id'),
        is_active=True
    )

    if UserSubscription.objects.filter(
        user=subscriber,
        plan=plan,
        payment_status='SUCCESS'
    ).exists():
        messages.error(
            request,
            'This plan is already paid for this subscriber.'
        )
        return redirect(
            'reporter_unpaid_subscriber_detail',
            user_id=subscriber.id
        )

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        messages.error(request, 'Razorpay keys are not configured.')
        return redirect(
            'reporter_unpaid_subscriber_detail',
            user_id=subscriber.id
        )

    try:
        create_razorpay_subscription_order(
            request,
            subscriber,
            plan,
            request.user.mobile or ''
        )
    except requests.RequestException:
        messages.error(request, 'Unable to create Razorpay order.')
        return redirect(
            'reporter_unpaid_subscriber_detail',
            user_id=subscriber.id
        )

    messages.success(request, 'Payment link generated successfully.')
    return redirect(
        'reporter_unpaid_subscriber_detail',
        user_id=subscriber.id
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

    stored_order_id = subscription.razorpay_order_id or subscription.transaction_id

    if stored_order_id != order_id:
        mark_subscription_failed(subscription)
        return render(
            request,
            'subscriptions/payment_failed.html'
        )

    message = f'{stored_order_id}|{payment_id}'
    if verify_razorpay_signature(
        message,
        signature,
        settings.RAZORPAY_KEY_SECRET
    ):
        payment_entity = fetch_razorpay_payment(payment_id)
        update_subscription_payment_details(
            subscription,
            payment_id=payment_id,
            signature=signature,
            payment_entity=payment_entity
        )

        if (
            payment_entity and
            payment_entity.get('status') != 'captured'
        ):
            return render(
                request,
                'subscriptions/payment_failed.html'
            )

        mark_subscription_success(
            subscription,
            payment_id=payment_id,
            signature=signature,
            payment_entity=payment_entity
        )
        invoice = get_or_create_invoice(subscription)
        clear_subscription_customer_session(request, subscription.user_id)
        return render(
            request,
            'subscriptions/payment_success.html',
            {
                'subscription': subscription,
                'invoice': invoice,
            }
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

    event_id = event.get('id') or ''
    event_name = event.get('event')
    if event_id and PaymentWebhookLog.objects.filter(event_id=event_id).exists():
        return HttpResponse(status=200)

    payment = (
        event.get('payload', {})
        .get('payment', {})
        .get('entity', {})
    )
    order = (
        event.get('payload', {})
        .get('order', {})
        .get('entity', {})
    )
    refund = (
        event.get('payload', {})
        .get('refund', {})
        .get('entity', {})
    )
    dispute = (
        event.get('payload', {})
        .get('dispute', {})
        .get('entity', {})
    )
    order_id = payment.get('order_id') or order.get('id')
    payment_id = payment.get('id')
    subscription = None

    if order_id:
        subscription = (
            UserSubscription.objects
            .filter(transaction_id=order_id)
            .first()
        )

    webhook_log = PaymentWebhookLog.objects.create(
        event_id=event_id,
        event_name=event_name or '',
        razorpay_payment_id=(
            payment_id or
            refund.get('payment_id') or
            dispute.get('payment_id') or
            ''
        ),
        razorpay_order_id=order_id or '',
        subscription=subscription,
        signature=signature or '',
        payload=event
    )

    if event_name in ('payment.captured', 'order.paid') and order_id:
        if subscription:
            mark_subscription_success(
                subscription,
                payment_id=payment_id,
                payment_entity=payment
            )
            webhook_log.processed = True
            webhook_log.processing_note = 'Subscription marked successful.'
        else:
            webhook_log.processing_note = 'No subscription found for order.'

    elif event_name == 'payment.authorized' and order_id:
        if subscription:
            update_subscription_payment_details(
                subscription,
                payment_id=payment_id,
                payment_entity=payment
            )
            webhook_log.processed = True
            webhook_log.processing_note = (
                'Payment authorized. Waiting for captured status before activation.'
            )
        else:
            webhook_log.processing_note = 'No subscription found for order.'

    elif event_name == 'payment.failed' and order_id:
        if subscription:
            mark_subscription_failed(subscription)
            update_subscription_payment_details(
                subscription,
                payment_id=payment_id,
                payment_entity=payment
            )
            webhook_log.processed = True
            webhook_log.processing_note = 'Subscription marked failed.'
        else:
            webhook_log.processing_note = 'No subscription found for order.'

    elif event_name in ('refund.created', 'refund.processed', 'refund.failed'):
        payment_id = refund.get('payment_id') or payment_id
        subscription = (
            UserSubscription.objects
            .filter(razorpay_payment_id=payment_id)
            .first()
        )

        if subscription:
            status_map = {
                'refund.created': 'CREATED',
                'refund.processed': 'PROCESSED',
                'refund.failed': 'FAILED',
            }
            refund_amount = Decimal(refund.get('amount') or 0) / Decimal('100')
            refund_id = refund.get('id') or ''
            refund_defaults = {
                'subscription': subscription,
                'amount': refund_amount,
                'status': status_map.get(event_name, 'REQUESTED'),
                'reason': refund.get('notes', {}).get('reason', ''),
                'gateway_response': refund,
            }

            if event_name == 'refund.created':
                refund_defaults['requested_at'] = get_razorpay_datetime(
                    refund.get('created_at')
                ) or timezone.now()

            if event_name == 'refund.processed':
                refund_defaults['processed_at'] = get_razorpay_datetime(
                    refund.get('created_at')
                ) or timezone.now()

            if refund_id:
                refund_record, _ = RefundRecord.objects.update_or_create(
                    razorpay_refund_id=refund_id,
                    defaults=refund_defaults
                )
            else:
                refund_record = RefundRecord.objects.create(
                    razorpay_refund_id='',
                    **refund_defaults
                )

            if refund_record.status == 'PROCESSED':
                subscription.payment_status = 'REFUNDED'
                subscription.is_active = False
                subscription.save(
                    update_fields=[
                        'payment_status',
                        'is_active',
                        'updated_at',
                    ]
                )

            webhook_log.subscription = subscription
            webhook_log.processed = True
            webhook_log.processing_note = 'Refund record updated.'
        else:
            webhook_log.processing_note = 'No subscription found for refund.'

    elif event_name in (
        'payment.dispute.created',
        'payment.dispute.closed',
        'payment.dispute.under_review',
        'payment.dispute.won',
        'payment.dispute.lost',
    ):
        payment_id = dispute.get('payment_id') or payment_id
        subscription = (
            UserSubscription.objects
            .filter(razorpay_payment_id=payment_id)
            .first()
        )

        if subscription:
            status_map = {
                'payment.dispute.created': 'EVIDENCE_REQUIRED',
                'payment.dispute.under_review': 'EVIDENCE_SUBMITTED',
                'payment.dispute.won': 'WON',
                'payment.dispute.lost': 'LOST',
                'payment.dispute.closed': 'ACCEPTED',
            }
            dispute_amount = (
                Decimal(dispute.get('amount') or 0) /
                Decimal('100')
            )
            dispute_id = dispute.get('id') or ''
            dispute_defaults = {
                'subscription': subscription,
                'amount': dispute_amount,
                'status': status_map.get(event_name, 'OPEN'),
                'reason': dispute.get('reason') or dispute.get('description') or '',
                'notice_received_at': get_razorpay_datetime(
                    dispute.get('created_at')
                ) or timezone.now(),
                'response_due_at': get_razorpay_datetime(
                    dispute.get('respond_by')
                ),
                'final_result': dispute.get('status') or '',
            }

            if dispute_id:
                DisputeEvidence.objects.update_or_create(
                    razorpay_dispute_id=dispute_id,
                    defaults=dispute_defaults
                )
            else:
                DisputeEvidence.objects.create(
                    razorpay_dispute_id='',
                    **dispute_defaults
                )

            webhook_log.subscription = subscription
            webhook_log.processed = True
            webhook_log.processing_note = 'Dispute evidence record updated.'
        else:
            webhook_log.processing_note = 'No subscription found for dispute.'

    webhook_log.save(
        update_fields=[
            'subscription',
            'processed',
            'processing_note',
        ]
    )

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
            'invoice': invoice,
            'gst_breakup': calculate_inclusive_gst(invoice.amount),
        }
    )


@login_required
def invoice_pdf(request, invoice_number):
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'subscription',
            'subscription__plan',
            'subscription__user'
        ),
        invoice_number=invoice_number,
        subscription__user=request.user
    )
    response = render(
        request,
        'subscriptions/invoice_pdf.html',
        {
            'invoice': invoice,
            'gst_breakup': calculate_inclusive_gst(invoice.amount),
        }
    )
    response['Content-Disposition'] = (
        f'inline; filename="{invoice.invoice_number}.html"'
    )
    return response


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

    if subscription:
        ensure_paid_subscription_invoices([subscription])

    subscriptions = (
        UserSubscription.objects
        .select_related('plan', 'invoice')
        .filter(user=request.user)
        .order_by('-created_at')
    )
    subscriptions = unique_subscriptions_by_plan(subscriptions)
    subscriptions = ensure_paid_subscription_invoices(subscriptions)

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
    subscriptions = ensure_paid_subscription_invoices(subscriptions)

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

    return redirect('/epaper/')
