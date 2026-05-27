from django.contrib import admin
from .models import *


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'subscription_type',
        'price',
        'duration',
        'duration_type',
        'is_active'
    )

    list_filter = (
        'subscription_type',
        'duration_type',
        'is_active'
    )

    search_fields = (
        'name',
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'plan',
        'amount',
        'payment_status',
        'is_active',
        'start_date',
        'end_date'
    )

    list_filter = (
        'payment_status',
        'is_active'
    )

    search_fields = (
        'user__username',
        'transaction_id'
    )


@admin.register(MagazineOrder)
class MagazineOrderAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'mobile',
        'city',
        'payment_status',
        'created_at'
    )


@admin.register(EPaper)
class EPaperAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'published_date',
        'premium_only'
    )
