"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 2.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import pytz

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "un8&muaf=dz@9df^lgdu-*iu_&q+9#mcbmbs0^)l89^9w$3p#^"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = BASE_DIR != "/app"

BASE_BASE_DIR = os.path.dirname(BASE_DIR)

if DEBUG:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
        BASE_BASE_DIR, "sa-key.json"
    )
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/keys/sa-key.json"

LOGIN_URL = LOGIN_REDIRECT_URL = "/api/accounts/login/"

ALLOWED_HOSTS = ["*"]

# Mail
SENDGRID_API_KEY = os.getenv("sendgrid_key")
SENDGRID_SENDER = os.getenv("sendgrid_sender")
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True
SERVER_EMAIL = DEFAULT_FROM_EMAIL = SENDGRID_SENDER

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app.apps.AppConfig",
    "corsheaders",
    "channels",
    "django_eventstream",
]

ASGI_APPLICATION = "config.routing.application"

DATA_PATH = os.path.join(BASE_DIR, "volume") if DEBUG else "/volume"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django_grip.GripMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "app.middleware.DisableCSRF",
    "app.middleware.AutoLogout",
]

CORS_ORIGIN_WHITELIST = []
if DEBUG:
    CORS_ORIGIN_WHITELIST = ["http://localhost:8080"]
    CORS_ALLOW_METHODS = [
        "DELETE",
        "GET",
        "OPTIONS",
        "PATCH",
        "POST",
        "PUT",
    ]
    CORS_ALLOW_CREDENTIALS = True
    SESSION_COOKIE_SAMESITE = None
    EVENTSTREAM_ALLOW_ORIGIN = "http://localhost:8080"

EVENTSTREAM_ALLOW_CREDENTIALS = True
ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}
if not DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ.get("POSTGRES_DB", "database"),
            "USER": os.environ.get("POSTGRES_USER", "user"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "password"),
            "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

TZ_NAME = "America/New_York"
TZ = pytz.timezone(TZ_NAME)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticroot") if DEBUG else "/var/www/static"

DOWNLOADS_DIR = os.path.join(STATIC_ROOT, "downloads")
DOWNLOADS_URL = STATIC_URL + "downloads/"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PARSER_CLASSES": ("rest_framework.parsers.JSONParser",),
}

# if not DEBUG:
#     LOGGING = {
#         "version": 1,
#         "disable_existing_loggers": True,
#         "formatters": {
#             "verbose": {"format": "%(levelname)s [%(asctime)s] %(module)s %(message)s"},
#         },
#         "handlers": {
#             "console": {"level": "ERROR", "class": "logging.StreamHandler"},
#             "file": {
#                 "level": "INFO",
#                 "class": "logging.handlers.RotatingFileHandler",
#                 "filename": "/app/debug.log",
#                 "maxBytes": 1024000,
#                 "backupCount": 1,
#             },
#         },
#         "loggers": {
#             "django": {
#                 "handlers": ["file", "console"],
#                 "propagate": True,
#                 "level": "INFO",
#             },
#         },
#     }

MAX_CPU = 100  # cores
MAX_MEMORY = 500000  # MiB

MIN_CPU = 50  # mCPU
MIN_MEMORY = 50  # MiB
RESOURCE_LIMIT_MULTIPLIER = 2  # limits = x * requests

MIN_NODES = int(os.environ.get("minnodes", "3"))
MAX_NODES = int(os.environ.get("maxnodes", "9"))
