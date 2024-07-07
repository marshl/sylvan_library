"""
Module for all django settings
"""

import environ

root = environ.Path(__file__) - 3  # three folder back (/a/b/c/ - 3 = /)
env = environ.Env(DEBUG=(bool, False))  # set default values and casting
environ.Env.read_env()  # reading .env file

SITE_ROOT = root()

DEBUG = env("DEBUG")  # False if not in os.environ
DEBUG_TOOLBAR = DEBUG and env("DEBUG_TOOLBAR")

DATABASES = {
    "default": env.db()  # Raises ImproperlyConfigured if DATABASE_URL not in os.environ
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# if (
#     "test" in sys.argv or "test_coverage" in sys.argv
# ):  # Covers regular testing and django-coverage
#     DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"

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
    # Django extension apps
    "rest_framework",
    "django_extensions",
    "djangoql",
    "django_select2",
    "tinymce",
    "widget_tweaks",
    # my apps
    "bitfield.apps.BitFieldAppConfig",
    "cards.apps.CardsConfig",
    "cardsearch.apps.CardsearchConfig",
    "data_export.apps.DataExportConfig",
    "data_import.apps.DataImportConfig",
    "reports.apps.ReportsConfig",
    "website.apps.WebsiteConfig",
    "frontend.apps.FrontendConfig",
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

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

# Disable browsable API when in production
if not DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
        "rest_framework.renderers.JSONRenderer",
    )

# LOGGING = {
#     "version": 1,
#     "filters": {"require_debug_true": {"()": "django.utils.log.RequireDebugTrue"}},
#     "handlers": {
#         "console": {
#             "level": "DEBUG",
#             "filters": ["require_debug_true"],
#             "class": "logging.StreamHandler",
#         }
#     },
#     "loggers": {"django.db.backends": {"level": "DEBUG", "handlers": ["console"]}},
# }
