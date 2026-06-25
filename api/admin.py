from django.contrib import admin
from .models import AppVersion


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = (
        "latest_version",
        "min_supported_version",
        "force_update",
        "update_available",
        "is_active",
        "updated_at",
    )

    list_editable = (
        "force_update",
        "update_available",
        "is_active",
    )

    search_fields = ("latest_version",)