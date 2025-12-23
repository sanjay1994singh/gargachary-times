from django.shortcuts import render

from video.models import Video

from news.models import News

from account.models import User

from category.models import Category

# Create your views here.
import requests

API_KEY = 'AIzaSyCzsOJL0XQHTuSc7MgiR_HkJeeOrks4UhI'
CHANNEL_ID = 'UC8eaQTAUBKj_OrNmXThrvbQ'


def get_youtube_videos(max_results=20):
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'key': API_KEY,
        'channelId': CHANNEL_ID,
        'part': 'snippet',
        'order': 'date',
        'maxResults': max_results,
        'type': 'video'
    }

    response = requests.get(url, params=params)
    data = response.json()
    videos = []
    for item in data.get('items', []):
        video_id = item['id']['videoId']
        title = item['snippet']['title']
        thumbnail = item['snippet']['thumbnails']['high']['url']
        published = item['snippet']['publishedAt']
        videos.append({
            'video_id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'publishedAt': published,
            'url': f'https://www.youtube.com/watch?v={video_id}'
        })
    return videos


def video(request):
    videos = get_youtube_videos()
    context = {
        'videos': videos,
    }
    return render(request, 'video.html', context)


def homepage(request):
    all_news = list(News.objects.all().order_by('-id')[:30])

    # Split into 3 parts
    column_2 = all_news[:8]  # latest 10
    column_1 = all_news[10:20]  # next 10
    column_3 = all_news[20:30]  # last 10

    context = {
        'news_col1': column_1,
        'news_col2': column_2,
        'news_col3': column_3,
    }
    return render(request, 'index.html', context)


def contact(request):
    return render(request, 'contact.html')


def category_news(request, id):
    category_name = Category.objects.get(id=id)
    all_news = list(News.objects.filter(category_id=id).order_by('-id')[:30])

    # Split into 3 parts
    column_2 = all_news[:10]  # latest 10
    column_1 = all_news[10:20]  # next 10
    column_3 = all_news[20:30]  # last 10

    context = {
        'news_col1': column_1,
        'news_col2': column_2,
        'news_col3': column_3,
        'category_name': category_name,
    }
    return render(request, 'category_news.html', context)
