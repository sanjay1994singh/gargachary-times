from django.shortcuts import render

from video.models import Video

from news.models import News, Visitor

from account.models import User
from django.http import HttpResponse

import csv
from category.models import Category
import requests
from django.utils import timezone
from datetime import timedelta


# Create your views here.
def dashboard(request):
    today = timezone.now().date()

    daily_visitors = Visitor.objects.filter(
        visited_at__date=today
    ).count()

    weekly_visitors = Visitor.objects.filter(
        visited_at__gte=timezone.now() - timedelta(days=7)
    ).count()

    monthly_visitors = Visitor.objects.filter(
        visited_at__gte=timezone.now() - timedelta(days=30)
    ).count()

    yearly_visitors = Visitor.objects.filter(
        visited_at__gte=timezone.now() - timedelta(days=365)
    ).count()

    total_news = News.objects.count()

    top_news = News.objects.order_by('-count')[:10]

    latest_news = News.objects.order_by('-created_at')[:5]

    # Last 7 days visitor chart
    chart_labels = []
    chart_data = []

    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)

        visitors = Visitor.objects.filter(
            visited_at__date=day
        ).count()

        chart_labels.append(day.strftime("%d %b"))
        chart_data.append(visitors)

    context = {
        'daily_visitors': daily_visitors,
        'weekly_visitors': weekly_visitors,
        'monthly_visitors': monthly_visitors,
        'yearly_visitors': yearly_visitors,
        'total_news': total_news,
        'top_news': top_news,
        'latest_news': latest_news,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }

    return render(request, 'dashboard.html', context)


def download_visitors_data(request):
    response = HttpResponse(
        content_type='text/csv'
    )

    response[
        'Content-Disposition'
    ] = 'attachment; filename="visitors_data.csv"'

    writer = csv.writer(response)

    writer.writerow([
        'ID',
        'IP Address',
        'Visited At'
    ])

    visitors = Visitor.objects.all().order_by('-visited_at')

    for visitor in visitors:
        writer.writerow([

            visitor.id,
            visitor.ip_address,
            visitor.visited_at

        ])

    return response


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
    all_news = list(News.objects.filter(category_id=id).order_by('-id'))

    # Split into 3 parts
    # column_2 = all_news[:10]  # latest 10
    # column_1 = all_news[10:20]  # next 10
    # column_3 = all_news[20:30]  # last 10

    context = {
        # 'news_col1': column_1,
        # 'news_col2': column_2,
        # 'news_col3': column_3,
        'all_news': all_news,
        'category_name': category_name,
    }
    return render(request, 'category_news.html', context)
