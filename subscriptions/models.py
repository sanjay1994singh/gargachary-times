from django.db import models
from django.conf import settings
from django.utils import timezone

from dateutil.relativedelta import relativedelta


SUBSCRIPTION_TYPES = (

    ('news', 'News'),

    ('magazine', 'Magazine'),

)


DURATION_TYPES = (

    ('days', 'Days'),

    ('months', 'Months'),

    ('years', 'Years'),

    ('lifetime', 'Lifetime'),

)


PAYMENT_STATUS = (

    ('PENDING', 'Pending'),

    ('SUCCESS', 'Success'),

    ('FAILED', 'Failed'),

    ('REFUNDED', 'Refunded'),

)


DELIVERY_STATUS = (
    ('NOT_REQUIRED', 'Not Required'),
    ('PENDING', 'Pending'),
    ('PROCESSING', 'Processing'),
    ('SHIPPED', 'Shipped'),
    ('DELIVERED', 'Delivered'),
    ('CANCELLED', 'Cancelled'),
)


class SubscriptionPlan(models.Model):

    name = models.CharField(
        max_length=200
    )

    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TYPES
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    duration = models.PositiveIntegerField(
        default=1
    )

    duration_type = models.CharField(
        max_length=20,
        choices=DURATION_TYPES,
        default='months'
    )

    description = models.TextField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        if self.duration_type == 'lifetime':

            return (
                f"{self.name}"
                f" - Lifetime"
            )

        return (
            f"{self.name}"
            f" - "
            f"{self.duration}"
            f" "
            f"{self.duration_type}"
        )


class UserSubscription(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    transaction_id = models.CharField(
        max_length=255,
        unique=True
    )

    razorpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True
    )

    razorpay_payment_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True
    )

    razorpay_signature = models.CharField(
        max_length=255,
        blank=True
    )

    razorpay_receipt = models.CharField(
        max_length=80,
        blank=True
    )

    payment_method = models.CharField(
        max_length=50,
        blank=True
    )

    currency = models.CharField(
        max_length=10,
        default='INR'
    )

    gateway_response = models.JSONField(
        default=dict,
        blank=True
    )

    reporter_mobile = models.CharField(
        max_length=20,
        blank=True,
        help_text='Mobile number of the reporter who sold this subscription.'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='PENDING'
    )

    is_active = models.BooleanField(
        default=False
    )

    start_date = models.DateTimeField(
        default=timezone.now
    )

    end_date = models.DateTimeField(
        blank=True,
        null=True
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True
    )

    captured_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        if not self.end_date:

            if self.plan.duration_type == 'days':

                self.end_date = (
                    self.start_date +
                    relativedelta(
                        days=self.plan.duration
                    )
                )

            elif self.plan.duration_type == 'months':

                self.end_date = (
                    self.start_date +
                    relativedelta(
                        months=self.plan.duration
                    )
                )

            elif self.plan.duration_type == 'years':

                self.end_date = (
                    self.start_date +
                    relativedelta(
                        years=self.plan.duration
                    )
                )

            elif self.plan.duration_type == 'lifetime':

                self.end_date = None

        super().save(*args, **kwargs)

    @property
    def is_valid(self):

        if self.end_date is None:
            return True

        return (
            self.end_date >= timezone.now()
        )

    def __str__(self):

        return (
            f"{self.user.username}"
            f" - "
            f"{self.plan.name}"
        )


class Invoice(models.Model):
    subscription = models.OneToOneField(
        UserSubscription,
        on_delete=models.CASCADE,
        related_name='invoice'
    )

    invoice_number = models.CharField(
        max_length=40,
        unique=True
    )

    billing_name = models.CharField(
        max_length=150
    )

    billing_email = models.EmailField(
        blank=True
    )

    billing_mobile = models.CharField(
        max_length=20,
        blank=True
    )

    billing_address = models.TextField(
        blank=True
    )

    billing_city = models.CharField(
        max_length=50,
        blank=True
    )

    billing_state = models.CharField(
        max_length=50,
        blank=True
    )

    billing_pincode = models.CharField(
        max_length=10,
        blank=True
    )

    billing_country = models.CharField(
        max_length=50,
        default='India'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS,
        default='PENDING'
    )

    delivery_note = models.CharField(
        max_length=255,
        blank=True
    )

    service_confirmed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='When the subscribed service/access was confirmed delivered.'
    )

    customer_notified_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='When payment/invoice confirmation was sent to the customer.'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.invoice_number


class PaymentWebhookLog(models.Model):
    event_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True
    )

    event_name = models.CharField(
        max_length=100,
        db_index=True
    )

    razorpay_payment_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True
    )

    razorpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True
    )

    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='webhook_logs'
    )

    signature = models.CharField(
        max_length=255,
        blank=True
    )

    payload = models.JSONField(
        default=dict,
        blank=True
    )

    processed = models.BooleanField(
        default=False
    )

    processing_note = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.event_name} - {self.razorpay_order_id or self.event_id}'


class RefundRecord(models.Model):
    REFUND_STATUS = (
        ('REQUESTED', 'Requested'),
        ('CREATED', 'Created'),
        ('PROCESSED', 'Processed'),
        ('FAILED', 'Failed'),
    )

    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.CASCADE,
        related_name='refunds'
    )

    razorpay_refund_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=REFUND_STATUS,
        default='REQUESTED'
    )

    reason = models.TextField(
        blank=True
    )

    gateway_response = models.JSONField(
        default=dict,
        blank=True
    )

    customer_notified_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.razorpay_refund_id or f'Refund for {self.subscription_id}'


class DisputeEvidence(models.Model):
    DISPUTE_STATUS = (
        ('OPEN', 'Open'),
        ('EVIDENCE_REQUIRED', 'Evidence Required'),
        ('EVIDENCE_SUBMITTED', 'Evidence Submitted'),
        ('WON', 'Won'),
        ('LOST', 'Lost'),
        ('ACCEPTED', 'Accepted'),
    )

    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.CASCADE,
        related_name='disputes'
    )

    razorpay_dispute_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=30,
        choices=DISPUTE_STATUS,
        default='OPEN'
    )

    reason = models.CharField(
        max_length=255,
        blank=True
    )

    response_due_at = models.DateTimeField(
        blank=True,
        null=True
    )

    billing_proof = models.TextField(
        blank=True,
        help_text='Invoice, receipt, order confirmation or payment proof.'
    )

    proof_of_service = models.TextField(
        blank=True,
        help_text='Subscription activation, access, delivery or service proof.'
    )

    customer_communication = models.TextField(
        blank=True,
        help_text='Email, SMS, WhatsApp or support communication proof.'
    )

    access_activity_log = models.TextField(
        blank=True,
        help_text='Login/download/access logs for digital delivery.'
    )

    refund_policy_snapshot = models.TextField(
        blank=True,
        help_text='Refund/cancellation policy shown to the customer.'
    )

    explanation = models.TextField(
        blank=True
    )

    evidence_submitted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.razorpay_dispute_id or f'Dispute for {self.subscription_id}'


class MagazineOrder(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(
        max_length=200
    )

    mobile = models.CharField(
        max_length=20
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100
    )

    district = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100
    )

    pincode = models.CharField(
        max_length=10
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    payment_status = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.full_name


class EPaper(models.Model):

    title = models.CharField(
        max_length=200
    )

    pdf = models.FileField(
        upload_to='epapers/'
    )

    cover_image = models.ImageField(
        upload_to='epaper_cover/'
    )

    published_date = models.DateField()

    premium_only = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.title
