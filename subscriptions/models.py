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

    created_at = models.DateTimeField(
        auto_now_add=True
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