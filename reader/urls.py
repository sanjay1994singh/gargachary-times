from django.urls import path

from . import views


app_name = "reader"

urlpatterns = [
    path("", views.reader_home, name="home"),
    path("upload/", views.upload_edition, name="upload"),
    path("edition/<int:pk>/", views.reader_home, name="edition"),
]
