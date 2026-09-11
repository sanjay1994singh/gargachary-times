from django.db import models
from django.contrib.auth.models import AbstractUser
from .passwords import get_mobile_password


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True)

    class Meta:
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name


class State(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='states'
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('country', 'name')
        ordering = ('name',)

    def __str__(self):
        return self.name


class User(AbstractUser):
    username = models.CharField(max_length=500, unique=True, null=True)
    user_type = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True)
    full_name = models.CharField(max_length=150, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=50, null=True)
    district = models.CharField(max_length=50, null=True)
    state = models.CharField(max_length=50, null=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=50, default='India')
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self._state.adding and not self.is_staff and not self.is_superuser:
            mobile_password = get_mobile_password(self.mobile)
            if mobile_password:
                self.set_password(mobile_password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'
