import time

from django.conf import settings


def static_asset_version(request):
    version = settings.STATIC_ASSET_VERSION or str(int(time.time()))

    return {
        'static_asset_version': version,
    }
