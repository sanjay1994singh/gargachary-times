from django.contrib import admin
from .models import Country, State, User


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'username',
        'email',
        'full_name',
        'mobile',
        'city',
        'state',
        'country'
    ]


admin.site.register(User, UserAdmin)
admin.site.register(Country)
admin.site.register(State)
