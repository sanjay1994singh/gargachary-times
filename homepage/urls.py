from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('category_news/<int:id>/', views.category_news, name='category_news'),
]
