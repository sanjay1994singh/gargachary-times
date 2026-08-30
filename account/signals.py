from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


TRIMMED_FIELD_TYPES = (
    models.CharField,
    models.TextField,
    models.EmailField,
)


@receiver(pre_save)
def strip_outer_whitespace(sender, instance, **kwargs):
    for field in instance._meta.fields:
        if not isinstance(field, TRIMMED_FIELD_TYPES):
            continue

        value = getattr(instance, field.attname, None)

        if isinstance(value, str):
            setattr(instance, field.attname, value.strip())
