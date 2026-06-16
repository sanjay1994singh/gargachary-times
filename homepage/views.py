from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

from video.models import Video

from news.models import News, Visitor

from account.models import User
from django.core.cache import cache

import csv
import threading
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

    top_news = News.objects.order_by('-count')[:3]

    latest_news = News.objects.order_by('-created_at')[:6]

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


def download_visitors_data(request, report_type):
    response = HttpResponse(
        content_type='text/csv'
    )

    response[
        'Content-Disposition'
    ] = f'attachment; filename="{report_type}_visitors_report.csv"'

    writer = csv.writer(response)

    writer.writerow([

        'ID',
        'IP Address',
        'City',
        'State',
        'Country',
        'Visited Date'

    ])

    today = timezone.now()

    if report_type == 'today':

        visitors = Visitor.objects.filter(
            visited_at__date=today.date()
        )

    elif report_type == 'yesterday':

        yesterday = today - timedelta(days=1)

        visitors = Visitor.objects.filter(
            visited_at__date=yesterday.date()
        )

    elif report_type == 'weekly':

        visitors = Visitor.objects.filter(
            visited_at__gte=today - timedelta(days=7)
        )

    elif report_type == 'monthly':

        visitors = Visitor.objects.filter(
            visited_at__gte=today - timedelta(days=30)
        )

    else:

        visitors = Visitor.objects.all()

    for visitor in visitors:
        writer.writerow([

            visitor.id,

            visitor.ip_address,

            visitor.city,

            visitor.state,

            visitor.country,

            visitor.visited_at.strftime(
                "%d-%m-%Y %H:%M"
            )

        ])

    return response


API_KEY = 'AIzaSyCJQ2WoCt9gMmdKlkaRS_NqEyNeNyxDm9k'
CHANNEL_HANDLE = 'Samachar24newschannel'
CHANNEL_ID = 'UC8eaQTAUBKj_OrNmXThrvbQ'
YOUTUBE_CACHE_SECONDS = 60 * 15
YOUTUBE_TIMEOUT_SECONDS = 4
HOMEPAGE_NEWS_CACHE_SECONDS = 60
HOMEPAGE_NEWS_LIMIT = 100
HOMEPAGE_CENTER_COLUMN_COUNT = 7
HOMEPAGE_LEFT_COLUMN_COUNT = 10
HOMEPAGE_RIGHT_COLUMN_PER_PAGE = 10


def get_youtube_channel_id():
    cache_key = f'youtube_channel_id:{CHANNEL_HANDLE}'
    cached_channel_id = cache.get(cache_key)

    if cached_channel_id:
        return cached_channel_id

    try:
        response = requests.get(
            'https://www.googleapis.com/youtube/v3/channels',
            params={
                'key': API_KEY,
                'part': 'id',
                'forHandle': CHANNEL_HANDLE,
            },
            timeout=YOUTUBE_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
        channel_id = data.get('items', [{}])[0].get('id')
    except (IndexError, requests.RequestException):
        channel_id = None

    channel_id = channel_id or CHANNEL_ID
    cache.set(cache_key, channel_id, YOUTUBE_CACHE_SECONDS)
    return channel_id


def get_youtube_videos(max_results=20, video_duration=None):
    channel_id = get_youtube_channel_id()
    cache_key = get_youtube_video_cache_key(
        channel_id,
        max_results,
        video_duration
    )
    cached_videos = cache.get(cache_key)

    if cached_videos is not None:
        return cached_videos

    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'key': API_KEY,
        'channelId': channel_id,
        'part': 'snippet',
        'order': 'date',
        'maxResults': max_results,
        'type': 'video'
    }

    if video_duration:
        params['videoDuration'] = video_duration

    try:
        response = requests.get(
            url,
            params=params,
            timeout=YOUTUBE_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return []

    videos = []
    for item in data.get('items', []):
        video_id = item.get('id', {}).get('videoId')
        snippet = item.get('snippet', {})
        title = snippet.get('title')
        thumbnail = (
                snippet.get('thumbnails', {}).get('high', {}).get('url')
                or snippet.get('thumbnails', {}).get('medium', {}).get('url')
                or snippet.get('thumbnails', {}).get('default', {}).get('url')
        )
        published = snippet.get('publishedAt')

        if not video_id or not title or not thumbnail:
            continue

        videos.append({
            'video_id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'publishedAt': published or '',
            'url': f'https://www.youtube.com/watch?v={video_id}'
        })

    cache.set(cache_key, videos, YOUTUBE_CACHE_SECONDS)
    return videos


def get_youtube_video_cache_key(channel_id, max_results, video_duration=None):
    return f'youtube_videos:{channel_id}:{max_results}:{video_duration or "all"}'


def get_cached_youtube_videos(max_results=4, video_duration=None):
    channel_ids = [
        cache.get(f'youtube_channel_id:{CHANNEL_HANDLE}'),
        CHANNEL_ID,
    ]

    for channel_id in dict.fromkeys(filter(None, channel_ids)):
        cached_videos = cache.get(
            get_youtube_video_cache_key(
                channel_id,
                max_results,
                video_duration
            )
        )

        if cached_videos is not None:
            return cached_videos

    refresh_key = f'youtube_refreshing:{max_results}:{video_duration or "all"}'

    if cache.add(refresh_key, True, 60):
        thread = threading.Thread(
            target=get_youtube_videos,
            kwargs={
                'max_results': max_results,
                'video_duration': video_duration,
            },
            daemon=True
        )
        thread.start()

    return []


def video(request):
    videos = get_youtube_videos()
    context = {
        'videos': videos,
    }
    return render(request, 'video.html', context)


def homepage(request):
    all_news = get_homepage_news()

    home_videos = get_cached_youtube_videos(max_results=4)

    column_2 = all_news[:HOMEPAGE_CENTER_COLUMN_COUNT]
    column_1_start = HOMEPAGE_CENTER_COLUMN_COUNT
    column_1_end = column_1_start + HOMEPAGE_LEFT_COLUMN_COUNT
    column_1 = all_news[column_1_start:column_1_end]
    page_obj = get_homepage_more_news_page(request.GET.get('page'))

    context = {
        'news_col1': column_1,
        'news_col2': column_2,
        'news_col3': page_obj.object_list,
        'page_obj': page_obj,
        'home_videos': home_videos,
    }

    return render(request, 'index.html', context)


def get_homepage_news():
    all_news = cache.get('homepage_latest_news_100')

    if all_news is None:
        all_news = list(
            News.objects.select_related('category')
            .order_by('-id')[:HOMEPAGE_NEWS_LIMIT]
        )
        cache.set(
            'homepage_latest_news_100',
            all_news,
            HOMEPAGE_NEWS_CACHE_SECONDS
        )

    return all_news


def get_homepage_more_news_page(page_number):
    all_news = get_homepage_news()
    right_column_start = HOMEPAGE_CENTER_COLUMN_COUNT + HOMEPAGE_LEFT_COLUMN_COUNT
    paginator = Paginator(
        all_news[right_column_start:],
        HOMEPAGE_RIGHT_COLUMN_PER_PAGE
    )
    return paginator.get_page(page_number)


def homepage_more_news(request):
    page_obj = get_homepage_more_news_page(request.GET.get('page'))
    html = render_to_string(
        'partials/homepage_more_news.html',
        {
            'news_col3': page_obj.object_list,
            'page_obj': page_obj,
        },
        request=request
    )
    return JsonResponse({
        'html': html,
        'page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    })


def contact(request):
    return render(request, 'contact.html')


def category_news(request, id):
    category_name = Category.objects.get(id=id)
    all_news = list(News.objects.filter(category_id=id).order_by('-id'))

    context = {
        'all_news': all_news,
        'category_name': category_name,
    }
    return render(request, 'category_news.html', context)


def privacy_policy(request):
    return render(request, 'pages/privacy_policy.html')


def privacy_app(request):
    return render(request, 'pages/privacy_app.html')


def disclaimer(request):
    return render(request, 'pages/disclaimer.html')


def refund_policy(request):
    return render(request, 'pages/refund_policy.html')


def terms_conditions(request):
    return render(request, 'pages/terms_conditions.html')


def shipping_policy(request):
    return render(request, 'pages/shipping_policy.html')


def contact_us(request):
    return render(request, 'pages/contact_us.html')
