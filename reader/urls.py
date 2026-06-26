from django.urls import path

from . import views


app_name = "reader"

urlpatterns = [
    path("", views.reader_home, name="home"),
    path("api/editions/", views.api_edition_list, name="api_edition_list"),
    path("api/editions/latest/", views.api_latest_edition, name="api_latest_edition"),
    path("api/editions/<int:pk>/", views.api_edition_detail, name="api_edition_detail"),
    path("upload/", views.upload_edition, name="upload"),
    path("edition/<int:pk>/", views.reader_home, name="edition"),
]
