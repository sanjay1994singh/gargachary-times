from django.urls import path
from . import views

urlpatterns = [
    path('', views.news_pdf, name='news_pdf'),
    path('news_pdf1/', views.news_pdf1, name='news_pdf1'),
]
