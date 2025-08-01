from django.urls import path
from . import views

urlpatterns = [
    path('reporter-user-login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('register-new-report/', views.register_new_report, name='register_new_report'),
    path('update-password/', views.update_password, name='update_password'),
]
