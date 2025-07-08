from django.urls import path
from . import views

urlpatterns = [
    path('news-detail/<int:id>/', views.news_detail, name='news_detail'),
]
