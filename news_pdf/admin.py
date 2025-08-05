from django.contrib import admin
from .models import NewsPDF


# Register your models here.
class NewsPDFAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']


admin.site.register(NewsPDF, NewsPDFAdmin)
