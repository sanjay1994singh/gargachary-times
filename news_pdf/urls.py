from django.urls import path
from . import views

urlpatterns = [
    path('', views.news_pdf, name='news_pdf'),
]
