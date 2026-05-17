from django.contrib import admin
from .models import News, Visitor


# Register your models here.
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'count', 'created_at', 'id']

class VisitorAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'city', 'state', 'country', 'id']


admin.site.register(News, NewsAdmin)
admin.site.register(Visitor, VisitorAdmin)
