import requests
from django.conf import settings


def post_to_facebook(news):
    url = f"https://graph.facebook.com/{settings.FACEBOOK_PAGE_ID}/feed"
    article_url = (
        f"{settings.SITE_URL}{news.get_absolute_url()}"
    )
    data = {
        "message": news.title,
        "link": article_url,
        "access_token": settings.FACEBOOK_ACCESS_TOKEN
    }

    response = requests.post(url, data=data)

    print(response.status_code)
    print(response.text)

    return response
