from django.contrib import admin
from .models import News


# Register your models here.
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'count', 'created_at', 'id']


admin.site.register(News, NewsAdmin)
