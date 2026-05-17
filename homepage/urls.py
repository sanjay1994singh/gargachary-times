from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('download-visitors-data/<str:report_type>/', views.download_visitors_data, name='download_visitors_data'),
    path('contact/', views.contact, name='contact'),
    path('video/', views.video, name='video'),
    path('category_news/<int:id>/', views.category_news, name='category_news'),
]
