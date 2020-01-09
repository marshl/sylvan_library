"""
Module for all django settings
"""

import sys
import environ
from elasticsearch_dsl.connections import connections

root = environ.Path(__file__) - 3  # three folder back (/a/b/c/ - 3 = /)
env = environ.Env(DEBUG=(bool, False))  # set default values and casting
environ.Env.read_env()  # reading .env file

connections.create_connection()

SITE_ROOT = root()

DEBUG = env("DEBUG")  # False if not in os.environ
DEBUG_TOOLBAR = DEBUG and env("DEBUG_TOOLBAR")

if (
    "test" in sys.argv or "test_coverage" in sys.argv
):  # Covers regular testing and django-coverage
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}
else:
    DATABASES = {
        "default": env.db()  # Raises ImproperlyConfigured if DATABASE_URL not in os.environ
    }

public_root = root.path("public/")

MEDIA_ROOT = public_root("media")
MEDIA_URL = "media/"
STATIC_ROOT = public_root("static")
STATIC_URL = "/static/"

# Raises ImproperlyConfigured exception if SECRET_KEY not in os.environ
SECRET_KEY = env("SECRET_KEY")

ROOT_URLCONF = "conf.urls"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "data_export",
    "data_import",
    "cardsearch",
    "cards",
    "django_extensions",
    "reports",
    "website",
    "widget_tweaks",
    "django_select2",
    "tinymce",
]

if DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
    INTERNAL_IPS = ("127.0.0.1", "localhost")

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

if DEBUG_TOOLBAR:
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

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
            ]
        },
    }
]

DATE_FORMAT = "Y-m-d"
