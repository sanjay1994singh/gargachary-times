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
