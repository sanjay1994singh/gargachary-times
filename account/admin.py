from django.contrib import admin
from .models import Country, State, User
from subscriptions.models import UserSubscription, user_has_successful_subscription


class UserSubscriptionInline(admin.TabularInline):
    model = UserSubscription
    extra = 0
    readonly_fields = (
        'plan',
        'amount',
        'transaction_id',
        'payment_status',
        'is_active',
        'start_date',
        'end_date',
        'created_at'
    )
    can_delete = False
    show_change_link = True


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
    search_fields = (
        'username',
        'email',
        'mobile',
        'full_name'
    )
    inlines = (
        UserSubscriptionInline,
    )

    def has_delete_permission(self, request, obj=None):
        if obj and user_has_successful_subscription(obj):
            return False

        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions


admin.site.register(User, UserAdmin)
admin.site.register(Country)
admin.site.register(State)
