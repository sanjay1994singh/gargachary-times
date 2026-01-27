from rest_framework import serializers
from .models import NewsPDF

class NewsPDFSerializer(serializers.ModelSerializer):
    featured_image = serializers.SerializerMethodField()
    pdf_file = serializers.SerializerMethodField()

    class Meta:
        model = NewsPDF
        fields = [
            'id',
            'title',
            'featured_image',
            'text',
            'pdf_file',
            'uploaded_at'
        ]

    def get_featured_image(self, obj):
        request = self.context.get('request')
        if obj.featured_image:
            return request.build_absolute_uri(obj.featured_image.url)
        return None

    def get_pdf_file(self, obj):
        request = self.context.get('request')
        if obj.pdf_file:
            return request.build_absolute_uri(obj.pdf_file.url)
        return None
