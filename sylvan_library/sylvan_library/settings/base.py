# Django settings for recruitment project.
import os
from os import path
from sylvan_library.settings.secrets import get_secret
import hashlib

BASE_DIR = path.dirname(path.dirname(os.path.abspath(__file__)))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': get_secret('DATABASE_NAME'),
        'USER': get_secret('DATABASE_USERNAME'),
        'PASSWORD': get_secret('DATABASE_PASSWORD'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 60 * 5, # Keeps connections for a maximum of 5 minutes.
        'HOST': '', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '', # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Australia/Canberra'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-AU'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Encryption key used for seekapi
#SEEK_ENCRYPTION_KEY = get_secret('SEEK_ENCRYPTION_KEY')
#SEEK_ENCRYPTION_HASH = hashlib.md5(SEEK_ENCRYPTION_KEY).digest()

# Additional locations of static files
#===============================================================================
# STATICFILES_DIRS = (
#     # Put strings here, like "/home/html/static" or "C:/www/django/static".
#     # Always use forward slashes, even on Windows.
#     # Don't forget to use absolute paths, not relative paths.
#     ('js', BASE_DIR.child('static', 'js')),
#     ('img', BASE_DIR.child('static', 'img')),
#     ('css', BASE_DIR.child('static', 'css')),
#     ('css', BASE_DIR.child('static', 'img')),
#     ('css', BASE_DIR.child('core', 'assets', 'css')),
#     ('js', BASE_DIR.child('core', 'assets', 'js')),
#     ('img', BASE_DIR.child('core', 'assets', 'img')),
#     ('css', BASE_DIR.child('core', 'assets', 'img')),
#     ('js', BASE_DIR.child('correspondence', 'assets', 'js')),
#     ('css', BASE_DIR.child('assessment', 'assets', 'css')),
#     ('js', BASE_DIR.child('assessment', 'assets', 'js')),
#     ('font', BASE_DIR.child('static', 'font'))
# )
#===============================================================================

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = get_secret('SECRET_KEY')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'tz_detect.middleware.TimezoneMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TZ_DETECT_COUNTRIES = ('AU')

ROOT_URLCONF = 'sylvan_library.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'sylvan_library.wsgi.application'

# TEMPLATE_DIRS = (
    # # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # # Always use forward slashes, even on Windows.
    # # Don't forget to use absolute paths, not relative paths.
    # BASE_DIR.child('templates'),
    # BASE_DIR.child('authentication', 'templates'),
    # BASE_DIR.child('core', 'templates'),
    # BASE_DIR.child('correspondence', 'templates'),
    # BASE_DIR.child('assessment', 'templates'),
    # BASE_DIR.child('emailimport', 'templates'),
    # BASE_DIR.child('notification', 'templates'),
    # BASE_DIR.child('seekapi', 'templates'),
# )

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'spellbook.apps.SpellbookConfig'
]

# AUTHENTICATION_BACKENDS = (
    # 'social.backends.google.GoogleOpenId',
    # 'django.contrib.auth.backends.ModelBackend',
# )

# TEMPLATE_CONTEXT_PROCESSORS = (
    # 'django.contrib.auth.context_processors.auth',
    # 'django.core.context_processors.debug',
    # 'django.core.context_processors.i18n',
    # 'django.core.context_processors.media',
    # 'django.core.context_processors.static',
    # 'django.core.context_processors.tz',
    # 'django.contrib.messages.context_processors.messages',
    # 'social.apps.django_app.context_processors.backends',
    # 'social.apps.django_app.context_processors.login_redirect',
    # 'core.context_processors.config',
    # 'notification.context_processors.user_notifications',
    # 'django.core.context_processors.request',
# )

#SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

STATIC_URL = '/static/'

#LOGIN_URL = '/login'
#LOGIN_REDIRECT_URL = '/applications/'

#MAIL_NUMBER_ATTEMPTS = 10

#AJAX_SLOW_POLL_INTERVAL_MILLISECONDS = 60000 # 1 minute
#DEFAULT_NOTIFICATIONS_TO_DISPLAY_COUNT = 10

# SITE_CONFIG = {
    # 'fivium.com.au': {
        # 'reply_to_email': 'recruitment@fivium.co.uk',
    # },
    # 'across.co.uk': {
        # 'reply_to_email': 'recruitment@across.co.uk',
    # },
# }

#SITE_CONFIG_CHOICES = ()

#for i in SITE_CONFIG.keys():
#    SITE_CONFIG_CHOICES += ((i, i),)
