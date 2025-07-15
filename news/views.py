from django.shortcuts import render

from django.contrib.auth import authenticate, login, logout
from news.models import News
from django.db.models import Q
from account.models import User
from django.http import JsonResponse

from category.models import Category


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


def news_panel(request):
    news = News.objects.get(id=1)
    try:
        absolute_image_url = request.build_absolute_uri(news.featured_image.url)
    except:
        absolute_image_url = ''

    context = {
        'news': news,
        'absolute_image_url': absolute_image_url,
    }
    return render(request, 'news_detail.html', context)


def user_news_list(request):
    news = News.objects.all().order_by('-id')
    return render(request, 'user_new_list.html', {'news': news})


def upload_news(request):
    category = Category.objects.all().order_by('-id')
    news = News.objects.all().order_by('-id')
    context = {
        'news': news,
        'category': category,
    }
    return render(request, 'upload_news.html', context)
