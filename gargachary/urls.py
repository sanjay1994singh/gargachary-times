from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from news.sitemap import NewsSitemap, CategorySitemap
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from account import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('homepage.urls')),
    path('video/', include('video.urls')),
    path('news/', include('news.urls')),
    path('account/', include('account.urls')),
    path('news_pdf/', include('news_pdf.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('auth/', include('social_django.urls', namespace='social')),

    path('reader/', include("reader.urls")),

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
