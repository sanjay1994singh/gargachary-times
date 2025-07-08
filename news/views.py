from django.shortcuts import render

from news.models import News


# Create your views here.
def news_detail(request, id):
    news = News.objects.get(id=id)
    try:
        absolute_image_url = request.build_absolute_uri(news.featured_image.url)
    except:
        absolute_image_url = ''

    context = {
        'news': news,
        'absolute_image_url': absolute_image_url,
    }
    return render(request, 'news_detail.html', context)
