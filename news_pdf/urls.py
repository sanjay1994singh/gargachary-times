from django.urls import path
from . import views

urlpatterns = [
    path('new_news_pdf/', views.new_news_pdf, name='new_news_pdf'),
    path('api/epaper/', views.epaper_list, name='epaper_list'),
]
