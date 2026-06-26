from urllib.parse import urljoin, urlparse

from django.conf import settings
from rest_framework import serializers

from .models import Edition, EditionPage


def absolute_media_url(request, url):
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return url

    site_url = getattr(settings, "SITE_URL", "").strip().rstrip("/")
    if site_url and "localhost" not in site_url and "127.0.0.1" not in site_url:
        return urljoin(f"{site_url}/", url.lstrip("/"))

    return request.build_absolute_uri(url) if request else url


class EditionPageSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = EditionPage
        fields = [
            "id",
            "number",
            "title",
            "image",
        ]

    def get_title(self, obj):
        return f"Page {obj.number:02d}"

    def get_image(self, obj):
        request = self.context.get("request")
        return absolute_media_url(request, obj.image.url if obj.image else "")


class EditionListSerializer(serializers.ModelSerializer):
    pdf = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    page_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Edition
        fields = [
            "id",
            "city",
            "section",
            "publish_date",
            "pdf",
            "thumbnail",
            "page_count",
            "created_at",
        ]

    def get_pdf(self, obj):
        request = self.context.get("request")
        return absolute_media_url(request, obj.pdf.url if obj.pdf else "")

    def get_thumbnail(self, obj):
        request = self.context.get("request")
        pages = list(obj.pages.all())
        first_page = pages[0] if pages else None
        return absolute_media_url(
            request,
            first_page.image.url if first_page and first_page.image else ""
        )


class EditionDetailSerializer(EditionListSerializer):
    pages = EditionPageSerializer(many=True, read_only=True)

    class Meta(EditionListSerializer.Meta):
        fields = EditionListSerializer.Meta.fields + [
            "pages",
        ]
