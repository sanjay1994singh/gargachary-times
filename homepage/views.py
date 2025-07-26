from django.shortcuts import render

from video.models import Video

from news.models import News

from account.models import User

from category.models import Category


# Create your views here.
def homepage(request):
    user_id = request.session.get('user_id')
    breaking_video = Video.objects.all().order_by('-id')
    news = News.objects.all().order_by('-id')[:7]
    category = Category.objects.all().order_by('-id')
    context = {
        'breaking_video': breaking_video,
        'news': news,
        'category': category,
    }
    return render(request, 'index1.html', context)
