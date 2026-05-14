from django.contrib.sitemaps import Sitemap
from .models import News
from category.models import Category

class NewsSitemap(Sitemap):

    changefreq = "hourly"

    priority = 0.9

    def items(self):
        return News.objects.all().order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at or obj.created_at



class CategorySitemap(Sitemap):

    changefreq = "daily"

    priority = 0.7

    def items(self):
        return Category.objects.all().order_by('-created_at')

    def lastmod(self, obj):
        return obj.created_at