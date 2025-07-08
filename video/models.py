from django.db import models

from category.models import Category


# Create your models here.
class Video(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=500, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    featured_image = models.ImageField(upload_to='news_image', null=True, blank=True)
    video_file = models.FileField(upload_to='video_file', null=True, blank=True)
    count = models.IntegerField(default=0)
    reporter = models.CharField(max_length=100, default='Admin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return str(self.title)

    class Meta:
        db_table = 'video'
