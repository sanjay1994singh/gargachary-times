from django.shortcuts import render

from video.models import Video

from news.models import News

from account.models import User

from category.models import Category


# Create your views here.
def homepage(request):
    all_news = list(News.objects.all().order_by('-id')[:30])

    # Split into 3 parts
    column_2 = all_news[:10]  # latest 10
    column_1 = all_news[10:20]  # next 10
    column_3 = all_news[20:30]  # last 10

    context = {
        'news_col1': column_1,
        'news_col2': column_2,
        'news_col3': column_3,
    }
    return render(request, 'index1.html', context)


def category_news(request, id):
    category = Category.objects.get(id=id)
    all_news = list(News.objects.filter(category_id=id).order_by('-id')[:30])

    # Split into 3 parts
    column_2 = all_news[:10]  # latest 10
    column_1 = all_news[10:20]  # next 10
    column_3 = all_news[20:30]  # last 10

    context = {
        'news_col1': column_1,
        'news_col2': column_2,
        'news_col3': column_3,
        'category': category.name,
    }
    return render(request, 'category_news.html', context)
