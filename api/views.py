from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AppVersion


class AppVersionAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        version = AppVersion.objects.filter(is_active=True).order_by("-id").first()

        if not version:
            return Response({
                "success": False,
                "message": "App version not configured."
            }, status=404)

        return Response({
            "success": True,
            "latestVersion": version.latest_version,
            "minSupportedVersion": version.min_supported_version,
            "forceUpdate": version.force_update,
            "updateAvailable": version.update_available,
            "playStoreUrl": version.play_store_url,
            "title": version.title,
            "message": version.message,
        })