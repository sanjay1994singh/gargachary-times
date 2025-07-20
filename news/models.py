from django.db import models

from category.models import Category

from account.models import User


# Create your models here.
class News(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=500, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    featured_image = models.ImageField(upload_to='news_image', null=True, blank=True)
    count = models.IntegerField(default=0)
    reporter = models.CharField(max_length=100, default='Gargachary Times')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return str(self.title)

    class Meta:
        db_table = 'news'


class OtherNewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, null=True, blank=True)
    other_image = models.ImageField(upload_to='other_news_image', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return str(self.news.title)

    class Meta:
        db_table = 'other_news_image'
