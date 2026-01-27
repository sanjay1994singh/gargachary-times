from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from news.models import News
from django.db.models import Q
from account.models import User
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from category.models import Category, State
from django.db.models import Prefetch
import random
from .serializers import NewsSerializer
from category.serializers import CategorySerializer, StateSerializer
# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def news_list(request):
    news = News.objects.order_by('-created_at')[:10]
    serializer = NewsSerializer(news, many=True, context={'request': request})

    live_tv = 'https://legitpro.co.in:9898/samachar24/samachar24/embed.html'

    # States with city categories
    states = State.objects.prefetch_related(
        Prefetch(
            'category_set',
            queryset=Category.objects.filter(city=True).order_by('name')
        )
    ).order_by('name')

    states_serializer = StateSerializer(states, many=True)

    # Other categories
    other_categories = Category.objects.filter(city=False).order_by('name')
    other_categories_serializer = CategorySerializer(other_categories, many=True)
    print(states_serializer,'================states_serializer')
    print(other_categories_serializer.data,'================other_categories_serializer.data')
    return Response({
        "live_tv": live_tv,
        "news": serializer.data,
        "dropdown": states_serializer.data,
        "normal": other_categories_serializer.data
    })


def news_detail(request, id):
    news = News.objects.get(id=id)
    count = news.count
    number = random.randint(1, 5)
    total_count = int(number + count)
    news.count = total_count
    news.save()
    try:
        absolute_image_url = request.build_absolute_uri(news.featured_image.url)
    except:
        absolute_image_url = ''
    category = Category.objects.all().order_by('-id')
    context = {
        'news': news,
        'absolute_image_url': absolute_image_url,
        'category': category,
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


@login_required(login_url='/account/reporter-user-login/')
def user_news_list(request):
    news = News.objects.all().order_by('-id')
    return render(request, 'user_new_list.html', {'news': news})


def upload_news(request):
    user_id = request.session.get('user_id')
    if user_id:
        if request.method == 'POST':
            title = request.POST.get('title')
            text = request.POST.get('news_text')
            category_id = request.POST.get('news_category')
            image = request.FILES.get('file_image')

            news = News.objects.create(
                title=title,
                text=text,
                category_id=category_id,
                featured_image=image,
                user_id=user_id,
            )
            if news:
                msg = 'News submitted successfully!'
                status = 'success'
            else:
                msg = 'News submitted failed!!'
                status = 'failed'
            context = {
                'status': status,
                'news_id': news.id,
                'msg': msg,
            }
            return JsonResponse(context)

        else:
            category = Category.objects.all().order_by('-id')
            news = News.objects.all().order_by('-id')
            context = {
                'news': news,
                'category': category,
            }
            return render(request, 'upload_news.html', context)

    else:
        return redirect('/account/reporter-user-login')
