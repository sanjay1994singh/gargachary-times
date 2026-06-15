from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Edition, EditionPage


def delete_file(file_field):
    if file_field and file_field.name:
        file_field.delete(save=False)


@receiver(post_delete, sender=Edition)
def delete_edition_pdf(sender, instance, **kwargs):
    delete_file(instance.pdf)


@receiver(post_delete, sender=EditionPage)
def delete_page_image(sender, instance, **kwargs):
    delete_file(instance.image)


@receiver(pre_save, sender=Edition)
def delete_replaced_pdf(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = Edition.objects.get(pk=instance.pk)
    except Edition.DoesNotExist:
        return

    if old_instance.pdf and old_instance.pdf != instance.pdf:
        delete_file(old_instance.pdf)
