"""
Module for all django settings
"""

import environ

root = environ.Path(__file__) - 3  # three folder back (/a/b/c/ - 3 = /)
env = environ.Env(DEBUG=(bool, False), )  # set default values and casting
environ.Env.read_env()  # reading .env file

SITE_ROOT = root()

DEBUG = env('DEBUG')  # False if not in os.environ

DATABASES = {
    'default': env.db(),  # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
}

public_root = root.path('public/')

MEDIA_ROOT = public_root('media')
MEDIA_URL = 'media/'
STATIC_ROOT = public_root('static')
STATIC_URL = '/static/'

# Raises ImproperlyConfigured exception if SECRET_KEY not in os.environ
SECRET_KEY = env('SECRET_KEY')

ROOT_URLCONF = 'sylvan_library.urls'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'data_import',
    'cards',
    'django_extensions',
    'website',
    'widget_tweaks',
]

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

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