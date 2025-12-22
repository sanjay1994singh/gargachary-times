from django.urls import path
from . import views

urlpatterns = [
    path('', views.news_pdf, name='news_pdf'),
    path('new_news_pdf/', views.new_news_pdf, name='new_news_pdf'),
]
