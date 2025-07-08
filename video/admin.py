from django.contrib import admin

from .models import Video


# Create your models here.
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'count', 'created_at', 'id']


admin.site.register(Video, VideoAdmin)
