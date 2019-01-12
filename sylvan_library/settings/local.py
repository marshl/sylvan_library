# Settings file used for local development.
from __future__ import absolute_import
from datetime import datetime
from settings.base import *

DEBUG = True
# JIRA_ISSUE_COLLECTOR = False
ENABLE_VIRUS_SCAN = False

ALLOWED_HOSTS = ['*', ]

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_REPLY_TO_DOMAIN = 'localhost'
EMAIL_FROM_ADDRESS = 'recruitment@localhost'

# URL that this site is hosted on
# Do not include the trailing slash.
SERVER_URL = 'http://localhost:8000'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
# MEDIA_ROOT = BASE_DIR.child('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

log_file = path.abspath(__name__ + datetime.now().strftime('%Y_%m_%d') + '.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(message)s',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
        },
    }
}

# djang-debug-toolbar doesnt allow wildcards in the INTERNAL_IPS settings which
# is not very useful when running with vagrant as the host can change IP.
# The following function adds wildcard support, as taken from:
# http://dancarroll.org/blog/2011/01/debugging-django-dev-server/
from fnmatch import fnmatch


class glob_list(list):
    def __contains__(self, key):
        for elt in self:
            if fnmatch(key, elt): return True
        return False


# Required for django-debug-toolbar. When connecting to the recruitment system
# using the following IPs the debug-toolbar will be displayed.
INTERNAL_IPS = glob_list(['127.0.0.1', '10.0.*.*'])

INSTALLED_APPS += (
    # 'debug_toolbar',
    # 'template_timings_panel',
)
