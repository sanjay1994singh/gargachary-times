from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/news/add/', views.dashboard_news_form, name='dashboard_news_add'),
    path('dashboard/news/all/', views.dashboard_news_list, name='dashboard_news_list'),
    path('dashboard/news/<int:news_id>/edit/', views.dashboard_news_form, name='dashboard_news_edit'),
    path('dashboard/news/<int:news_id>/delete/', views.dashboard_news_delete, name='dashboard_news_delete'),
    path('dashboard/users/<str:user_type>/', views.dashboard_users, name='dashboard_users'),
    path('download-visitors-data/<str:report_type>/', views.download_visitors_data, name='download_visitors_data'),
    path('contact/', views.contact, name='contact'),
    path('video/', views.video, name='video'),
    path('homepage-more-news/', views.homepage_more_news, name='homepage_more_news'),
    path('category_news/<int:id>/', views.category_news, name='category_news'),

    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('privacy-app/', views.privacy_app, name='privacy_app'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('refund-policy/', views.refund_policy, name='refund_policy'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('terms-and-conditions/', views.terms_conditions, name='terms_conditions'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('contact-us/', views.contact_us, name='contact_us'),
]
