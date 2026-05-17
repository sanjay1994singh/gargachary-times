from django.db import models

from category.models import Category
from slugify import slugify
from account.models import User
from django.urls import reverse
import re


def hindi_slug(text):
    text = str(text).strip().lower()

    # keep Hindi + English + numbers + spaces
    text = re.sub(
        r'[^ऀ-ॿa-zA-Z0-9\s-]',
        '',
        text
    )

    # replace spaces with hyphen
    text = re.sub(r'[\s]+', '-', text)

    # remove duplicate hyphens
    text = re.sub(r'-+', '-', text)

    return text.strip('-')


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
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=700)

    def save(self, *args, **kwargs):

        if not self.slug:
            base_slug = hindi_slug(self.title)

            if not base_slug:
                base_slug = f'news-{self.id}'

            slug = base_slug
            counter = 1

            while News.objects.filter(
                    slug=slug
            ).exclude(
                id=self.id
            ).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):

        return reverse(
            'news_detail',
            kwargs={
                'id': self.id,
                'slug': self.slug
            }
        )

    def __str__(self):
        return str(self.title)

    class Meta:
        db_table = 'news'


class Visitor(models.Model):
    ip_address = models.GenericIPAddressField()
    visited_at = models.DateTimeField(auto_now_add=True)


class OtherNewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, null=True, blank=True)
    other_image = models.ImageField(upload_to='other_news_image', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return str(self.news.title)

    class Meta:
        db_table = 'other_news_image'
