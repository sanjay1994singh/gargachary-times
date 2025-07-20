from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from news.models import News
from django.db.models import Q
from account.models import User
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
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
