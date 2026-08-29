from django.urls import path

from . import views

urlpatterns = [

    path(
        'plans/',
        views.plans,
        name='plans'
    ),

    path(
        'subscribe/<int:plan_id>/',
        views.subscribe,
        name='subscribe'
    ),

    path(
        'reporters/create/',
        views.create_reporter_account,
        name='create_reporter_account'
    ),

    path(
        'reporter/unpaid-subscribers/',
        views.reporter_unpaid_subscribers,
        name='reporter_unpaid_subscribers'
    ),

    path(
        'reporter/success-subscribers/',
        views.reporter_success_subscribers,
        name='reporter_success_subscribers'
    ),

    path(
        'reporter/unpaid-subscribers/<int:user_id>/',
        views.reporter_unpaid_subscriber_detail,
        name='reporter_unpaid_subscriber_detail'
    ),

    path(
        'reporter/unpaid-subscribers/<int:user_id>/generate-payment/',
        views.reporter_generate_subscriber_payment,
        name='reporter_generate_subscriber_payment'
    ),

    path(
        'payment/<int:plan_id>/',
        views.phonepe_payment,
        name='phonepe_payment'
    ),

    path(
        'razorpay/order/<int:plan_id>/',
        views.razorpay_create_order,
        name='razorpay_create_order'
    ),

    path(
        'pay/<str:order_id>/',
        views.razorpay_shared_payment,
        name='razorpay_shared_payment'
    ),

    path(
        'razorpay/callback/',
        views.razorpay_payment_callback,
        name='razorpay_payment_callback'
    ),

    path(
        'razorpay/webhook/',
        views.razorpay_webhook,
        name='razorpay_webhook'
    ),

    path(
        'payment-callback/',
        views.payment_callback,
        name='payment_callback'
    ),

    path(
        'payment-success/',
        views.payment_success,
        name='payment_success'
    ),

    path(
        'payment-failed/',
        views.payment_failed,
        name='payment_failed'
    ),

    path(
        'invoice/<str:invoice_number>/',
        views.invoice_detail,
        name='invoice_detail'
    ),

    path(
        'profile/',
        views.profile,
        name='profile'
    ),

    path(
        'my-subscription/',
        views.my_subscription,
        name='my_subscription'
    ),

    path(
        'epaper/',
        views.epaper,
        name='epaper'
    ),

]
