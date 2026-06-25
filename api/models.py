from django.db import models


class AppVersion(models.Model):
    latest_version = models.CharField(max_length=20, default="1.0.1")
    min_supported_version = models.CharField(max_length=20, default="1.0.0")

    force_update = models.BooleanField(default=False)
    update_available = models.BooleanField(default=True)

    play_store_url = models.URLField(
        default="https://play.google.com/store/apps/details?id=com.gargacharytimes.app"
    )

    title = models.CharField(max_length=100, default="Update Available")
    message = models.TextField(
        default="Please update to continue using Gargacharya Times."
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.latest_version