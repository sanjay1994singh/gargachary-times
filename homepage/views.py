from django.shortcuts import render

from video.models import Video

from news.models import News

from account.models import User


# Create your views here.
def homepage(request):
    user = User.objects.all()
    print(user, '============user')
    breaking_video = Video.objects.all().order_by('-id')
    news = News.objects.all().order_by('-id')
    context = {
        'breaking_video': breaking_video,
        'news': news,
    }
    return render(request, 'index.html', context)
