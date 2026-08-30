from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from video.models import Video

from news.models import News, Visitor

from account.models import User
from django.core.cache import cache

import csv
import threading
from category.models import Category
import requests
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
from defusedxml import ElementTree


def is_admin_user(user):
    return (
        user.is_authenticated and
        (
            user.is_staff or
            user.is_superuser
        )
    )


def redirect_non_admin_dashboard_user(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.user_type == 'reporter':
        return redirect('reporter_unpaid_subscribers')

    return redirect('profile')


# Create your views here.
@login_required
def dashboard(request):
    if not is_admin_user(request.user):
        return redirect_non_admin_dashboard_user(request)

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


def get_dashboard_user_queryset(user_type, current_user=None):
    if current_user and not (
        current_user.is_staff or
        current_user.is_superuser
    ):
        if current_user.user_type == user_type:
            return User.objects.filter(id=current_user.id)

        return User.objects.none()

    if user_type == 'subscriber':
        return (
            User.objects
            .filter(user_type='subscriber')
            .order_by('-created_at')
        )

    if user_type == 'reporter':
        return (
            User.objects
            .filter(user_type='reporter')
            .order_by('-created_at')
        )

    return User.objects.none()


def dashboard_news_form(request, news_id=None):
    if not is_admin_user(request.user):
        return redirect_non_admin_dashboard_user(request)

    news_obj = None

    if news_id:
        news_obj = get_object_or_404(News, id=news_id)

    if request.method == 'POST':
        category_id = request.POST.get('news_category')
        title = request.POST.get('title')
        text = request.POST.get('news_text')
        reporter = request.POST.get('reporter') or 'Gargachary Times'
        image = request.FILES.get('file_image')

        if not news_obj:
            news_obj = News()

        news_obj.category_id = category_id or None
        news_obj.title = title
        news_obj.text = text
        news_obj.reporter = reporter

        if image:
            news_obj.featured_image = image

        if request.user.is_authenticated:
            news_obj.user = request.user

        news_obj.save()

        messages.success(request, 'News saved successfully.')
        return redirect('dashboard_news_list')

    reporter_users = (
        User.objects
        .filter(user_type='reporter')
        .order_by('full_name', 'username')
    )
    reporter_options = []

    for reporter_user in reporter_users:
        reporter_name = (
            reporter_user.full_name or
            reporter_user.username or
            reporter_user.email or
            reporter_user.mobile
        )

        if not reporter_name:
            continue

        reporter_options.append({
            'name': reporter_name,
            'mobile': reporter_user.mobile or '',
        })

    context = {
        'active_menu': 'news',
        'page_title': 'Edit News' if news_obj else 'Add News',
        'news_obj': news_obj,
        'category': Category.objects.all().order_by('-id'),
        'reporter_options': reporter_options,
    }

    return render(request, 'dashboard_news_form.html', context)


def dashboard_news_list(request):
    if not is_admin_user(request.user):
        return redirect_non_admin_dashboard_user(request)

    news_items = (
        News.objects
        .select_related('category', 'user')
        .order_by('-id')
    )
    paginator = Paginator(news_items, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    current_page = page_obj.number
    page_numbers = [
        page_number
        for page_number in paginator.page_range
        if current_page - 2 <= page_number <= current_page + 2
    ]

    return render(
        request,
        'dashboard_news_list.html',
        {
            'active_menu': 'news',
            'page_title': 'All News',
            'page_obj': page_obj,
            'page_numbers': page_numbers,
            'news_items': page_obj.object_list,
        }
    )


@require_POST
@login_required
def dashboard_news_delete(request, news_id):
    if not is_admin_user(request.user):
        return redirect_non_admin_dashboard_user(request)

    news_obj = get_object_or_404(News, id=news_id)
    news_obj.delete()
    messages.success(request, 'News deleted successfully.')
    return redirect('dashboard_news_list')


@login_required
def dashboard_users(request, user_type):
    if not is_admin_user(request.user):
        if request.user.user_type == 'reporter':
            return redirect('reporter_unpaid_subscribers')

        return redirect('profile')

    title_map = {
        'subscriber': 'Subscriber Accounts',
        'reporter': 'Reporter Accounts',
    }

    users = get_dashboard_user_queryset(user_type, request.user)

    return render(
        request,
        'dashboard_users.html',
        {
            'active_menu': 'users',
            'page_title': title_map.get(user_type, 'User Accounts'),
            'users': users,
            'user_type': user_type,
        }
    )


def download_visitors_data(request, report_type):
    if not is_admin_user(request.user):
        return redirect_non_admin_dashboard_user(request)

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


CHANNEL_HANDLE = 'Samachar24newschannel'
CHANNEL_ID = 'UC8eaQTAUBKj_OrNmXThrvbQ'
YOUTUBE_FEED_URL = (
    'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
)
YOUTUBE_CACHE_SECONDS = 60 * 15
YOUTUBE_TIMEOUT_SECONDS = 4
HOMEPAGE_NEWS_CACHE_SECONDS = 60
HOMEPAGE_NEWS_LIMIT = 100
HOMEPAGE_CENTER_COLUMN_COUNT = 7
HOMEPAGE_LEFT_COLUMN_COUNT = 10
HOMEPAGE_RIGHT_COLUMN_PER_PAGE = 10


def get_youtube_videos(max_results=20, video_duration=None):
    channel_id = CHANNEL_ID
    cache_key = get_youtube_video_cache_key(
        channel_id,
        max_results,
        video_duration
    )
    cached_videos = cache.get(cache_key)

    if cached_videos is not None:
        return cached_videos

    try:
        response = requests.get(
            YOUTUBE_FEED_URL.format(channel_id=channel_id),
            timeout=YOUTUBE_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
    except (ElementTree.ParseError, requests.RequestException):
        return []

    atom_namespace = '{http://www.w3.org/2005/Atom}'
    media_namespace = '{http://search.yahoo.com/mrss/}'
    yt_namespace = '{http://www.youtube.com/xml/schemas/2015}'
    videos = []
    entries = root.findall(f'{atom_namespace}entry')

    for item in entries[:max_results]:
        video_id = get_xml_text(item, f'{yt_namespace}videoId')
        title = get_xml_text(item, f'{atom_namespace}title')
        published = get_xml_text(item, f'{atom_namespace}published')
        media_group = item.find(f'{media_namespace}group')
        thumbnail = ''

        if media_group is not None:
            thumbnail_element = media_group.find(f'{media_namespace}thumbnail')
            if thumbnail_element is not None:
                thumbnail = thumbnail_element.attrib.get('url', '')

        if not video_id or not title or not thumbnail:
            continue

        videos.append({
            'video_id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'publishedAt': parse_datetime(published) if published else None,
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'embed_url': f'https://www.youtube.com/embed/{video_id}',
        })

    cache.set(cache_key, videos, YOUTUBE_CACHE_SECONDS)
    return videos


def get_youtube_video_cache_key(channel_id, max_results, video_duration=None):
    return f'youtube_videos:{channel_id}:{max_results}:{video_duration or "all"}'


def get_xml_text(element, path):
    child = element.find(path)
    if child is None or child.text is None:
        return ''

    return child.text.strip()


def get_cached_youtube_videos(max_results=4, video_duration=None):
    channel_ids = [
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
        'latest_video': videos[0] if videos else None,
        'channel_url': f'https://www.youtube.com/@{CHANNEL_HANDLE}',
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


def return_policy(request):
    return render(request, 'pages/return_policy.html')


def terms_conditions(request):
    return render(request, 'pages/terms_conditions.html')


def shipping_policy(request):
    return render(request, 'pages/shipping_policy.html')


def contact_us(request):
    return render(request, 'pages/contact_us.html')
