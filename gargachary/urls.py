from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from news.sitemap import NewsSitemap, CategorySitemap
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from account import views


def ads_txt(request):
    return HttpResponse(
        'google.com, pub-6716930239576338, DIRECT, f08c47fec0942fa0\n',
        content_type='text/plain'
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('ads.txt', ads_txt, name='ads_txt'),
    path('', include('homepage.urls')),
    path('video/', include('video.urls')),
    path('news/', include('news.urls')),
    path('account/', include('account.urls')),
    path('news_pdf/', include('news_pdf.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('auth/', include('social_django.urls', namespace='social')),
    path("api/", include("api.urls")),
    path('epaper/', include("reader.urls")),
    path(
        'reader/',
        RedirectView.as_view(pattern_name='reader:home', permanent=True)
    ),
    path(
        'reader/upload/',
        RedirectView.as_view(pattern_name='reader:upload', permanent=True)
    ),
    path(
        'reader/edition/<int:pk>/',
        RedirectView.as_view(pattern_name='reader:edition', permanent=True)
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'accounts/login/',
        views.login_view,
        name='accounts_login'
    ),

    path(
        'register/',
        views.register,
        name='register'
    ),
]

sitemaps = {

    'news': NewsSitemap,

    'categories': CategorySitemap,

}

urlpatterns += [

    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='sitemap'
    ),

    path(
        'robots.txt',
        TemplateView.as_view(
            template_name='robots.txt',
            content_type='text/plain'
        )
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
