from django.urls import path
from .views import AppVersionAPIView

urlpatterns = [
    path("version/", AppVersionAPIView.as_view(), name="app-version"),
]