from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('download-visitors-data/<str:report_type>/', views.download_visitors_data, name='download_visitors_data'),
    path('contact/', views.contact, name='contact'),
    path('video/', views.video, name='video'),
    path('category_news/<int:id>/', views.category_news, name='category_news'),

    path(
        'privacy-policy/',
        views.privacy_policy,
        name='privacy_policy'
    ),

    path(
        'privacy-app/',
        views.privacy_app,
        name='privacy_app'
    ),

    path(
        'disclaimer/',
        views.disclaimer,
        name='disclaimer'
    ),

    path(
        'refund-policy/',
        views.refund_policy,
        name='refund_policy'
    ),

    path(
        'terms-and-conditions/',
        views.terms_conditions,
        name='terms_conditions'
    ),

    path(
        'shipping-policy/',
        views.shipping_policy,
        name='shipping_policy'
    ),

    path(
        'contact-us/',
        views.contact_us,
        name='contact_us'
    ),
]
