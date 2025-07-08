from django.shortcuts import render

from video.models import Video


# Create your views here.
def video_detail(request, id):
    news = Video.objects.get(id=id)
    try:
        absolute_image_url = request.build_absolute_uri(news.featured_image.url)
    except:
        absolute_image_url = ''

    context = {
        'news': news,
        'absolute_image_url': absolute_image_url,
    }
    return render(request, 'video_detail.html', context)
