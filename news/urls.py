from django.urls import path
from . import views

urlpatterns = [
    path('news-detail/<int:id>/', views.news_detail, name='news_detail'),
    path('news-panel/', views.news_panel, name='news_panel'),
    path('user-news-list/', views.user_news_list, name='user_news_list'),
    path('upload-news/', views.upload_news, name='upload_news'),
]
