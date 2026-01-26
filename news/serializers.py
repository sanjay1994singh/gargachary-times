from rest_framework import serializers
from .models import News

class NewsSerializer(serializers.ModelSerializer):
    featured_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = News
        fields = [
            'id',
            'category_name',
            'title',
            'text',
            'featured_image',
            'reporter',
            'created_at'
        ]

    def get_featured_image(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.featured_image.url)
        return None
