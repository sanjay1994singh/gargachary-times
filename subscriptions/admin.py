from django.contrib import admin
from .models import *
from .views import send_delivery_status_email


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
        'user_email',
        'user_mobile',
        'reporter_mobile_display',
        'plan',
        'amount',
        'payment_status',
        'is_active',
        'invoice_number',
        'delivery_status',
        'start_date',
        'end_date'
    )

    list_filter = (
        'payment_status',
        'is_active',
        'plan',
        'reporter_mobile',
        'invoice__delivery_status'
    )

    search_fields = (
        'user__username',
        'user__email',
        'user__mobile',
        'reporter_mobile',
        'invoice__invoice_number',
        'transaction_id'
    )

    readonly_fields = (
        'created_at',
    )

    def user_email(self, obj):
        return obj.user.email

    def user_mobile(self, obj):
        return obj.user.mobile

    def reporter_mobile_display(self, obj):
        return obj.reporter_mobile or '-'

    reporter_mobile_display.short_description = 'Reporter mobile'

    def invoice_number(self, obj):
        return getattr(obj.invoice, 'invoice_number', '-')

    def delivery_status(self, obj):
        return getattr(obj.invoice, 'delivery_status', '-')


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


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number',
        'subscription',
        'billing_name',
        'billing_email',
        'billing_mobile',
        'amount',
        'delivery_status',
        'created_at'
    )

    list_filter = (
        'delivery_status',
        'subscription__payment_status',
        'created_at'
    )

    search_fields = (
        'invoice_number',
        'billing_email',
        'billing_mobile',
        'billing_name',
        'subscription__user__username',
        'subscription__user__email',
        'subscription__user__mobile',
        'subscription__transaction_id'
    )

    readonly_fields = (
        'invoice_number',
        'subscription',
        'amount',
        'billing_name',
        'billing_email',
        'billing_mobile',
        'billing_address',
        'billing_city',
        'billing_state',
        'billing_pincode',
        'billing_country',
        'created_at'
    )

    actions = (
        'send_delivery_update_email',
    )

    def send_delivery_update_email(self, request, queryset):
        sent_count = 0

        for invoice in queryset.select_related(
            'subscription',
            'subscription__user',
            'subscription__plan'
        ):
            send_delivery_status_email(invoice)
            sent_count += 1

        self.message_user(
            request,
            f'Delivery status email sent for {sent_count} invoice(s).'
        )

    send_delivery_update_email.short_description = (
        'Send delivery status email to selected users'
    )
