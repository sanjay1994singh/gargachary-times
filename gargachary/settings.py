import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_URL = 'https://gargacharytimes.in'
load_dotenv(BASE_DIR / ".env")
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# https://graph.facebook.com/v23.0/oauth/access_token?client_id=1545645713588372&client_secret=951603534d3c1038285458ea39530346&grant_type=fb_exchange_token&fb_exchange_token=EAAV9waZB1AJQBRt4RE369UZAvRYXIaty5PdGJe1UEIov8ZAmSgC1wMGLT9hmbhjQI3dNvdEDqZCiq0aeCvSDexq8JhpjFCiNcNjEm4cCICbmZC4prLq9g8DPt1nMaQZAuXPT2Ru42vYSBvrLHL2Q1KvdQYyuHXtVTZBT6WLb3JqGW1BGPxUacJlKG6nDRH4MfQfGg9ZC6m0Kj65F410UApi8TKGJfSNGZCOsMArwZBVS5AA2E7nuG2NpDjCrDTNmYZD

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',

    'reader',

    'social_django',
    'account',

    'category',
    'homepage',
    # 'news',
    'video',
    'news_pdf',
    'rest_framework',
    'subscriptions',

    'news.apps.NewsConfig',
]

SITE_ID = 1
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv("GOOGLE_CLIENT_ID")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)
FACEBOOK_PAGE_ID = "962106757151415"
FACEBOOK_ACCESS_TOKEN = "EAAO3ZAQYMxCMBRmKBUZC8CDtuTcBEeNb1m0UForAsGLTJPHE6OLRansUaYvfslvLJSaWydTgxOVE6Dib74ZC8VLBoZC8DLhZC4Qc3VqVQaC7CXeFMr0tcNs9rggU0AjaBrfe5ggsjiyiGsEfVTOevEPSZBqfWTGenvZC4l2t9YPmJwm3zekfnw9UsmUHKHR0jZAEZA33VabP42BbMOuAmcxKS"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'reader.middleware.EpaperMediaCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'news.middleware.VisitorMiddleware',
]

ROOT_URLCONF = 'gargachary.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'news.context_processors.category_context',

                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'gargachary.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'mbdb/db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'garga',
#         'USER': 'sanjay',
#         'PASSWORD': 'Hello12345678#$@',
#         'HOST': '145.223.18.243',
#         'PORT': '3306',
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = "account.User"

PHONEPE_MERCHANT_ID = os.getenv("PHONEPE_MERCHANT_ID")
PHONEPE_SALT_KEY = os.getenv("PHONEPE_SALT_KEY")
PHONEPE_SALT_INDEX = os.getenv("PHONEPE_SALT_INDEX")
PHONEPE_ENV = os.getenv("PHONEPE_ENV")
