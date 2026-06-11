from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import News
from .facebook import post_to_facebook


@receiver(post_save, sender=News)
def auto_post_news(sender, instance, created, **kwargs):

    if created:
        try:
            post_to_facebook(instance)
            print("Facebook post successful")

        except Exception as e:
            print("Facebook post failed:", e)