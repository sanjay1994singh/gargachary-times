from django.db.models.signals import post_save
from django.dispatch import receiver
import threading

from .models import News
from .facebook import post_to_facebook


def delayed_facebook_post(news_id):
    try:
        news = News.objects.get(id=news_id)

        post_to_facebook(news)

        print("Facebook post successful")

        News.objects.filter(
            pk=news.pk
        ).update(
            facebook_posted=True
        )

    except Exception as e:
        print("Facebook post failed:", e)


@receiver(post_save, sender=News)
def auto_post_news(sender, instance, created, **kwargs):
    if created:
        timer = threading.Timer(
            5.0,
            delayed_facebook_post,
            args=[instance.id]
        )

        timer.start()
