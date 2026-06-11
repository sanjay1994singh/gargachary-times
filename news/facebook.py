import requests
from django.conf import settings


def post_to_facebook(news):
    article_url = (
        f"{settings.SITE_URL}"
        f"{news.get_absolute_url()}"
    )

    message = f"{news.title}\n\n{article_url}"

    requests.post(
        f"https://graph.facebook.com/{settings.FACEBOOK_PAGE_ID}/feed",
        data={
            "message": message,
            "access_token": settings.FACEBOOK_ACCESS_TOKEN
        }
    )
