from django.contrib import admin
from .models import Category, State


# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'id']

class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'id']


admin.site.register(State, StateAdmin)
admin.site.register(Category, CategoryAdmin)
