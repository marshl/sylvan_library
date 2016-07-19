# Settings to be used in a production environment.
from __future__ import absolute_import

from .base import *


DEBUG = False
JIRA_ISSUE_COLLECTOR = False
ENABLE_VIRUS_SCAN = False

ALLOWED_HOSTS = ['www.rockitrecruit.com', 'static.rockitrecruit.com', 'rockitrecruit.com']

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = '587'
EMAIL_HOST_USER = get_secret('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_secret('EMAIL_HOST_PASSWORD')

SERVER_EMAIL = 'system@rockitrecruit.com'

EMAIL_FROM_ADDRESS = 'recruitment@fivium.co.uk'
EMAIL_REPLY_TO_DOMAIN = 'rockitrecruit.com'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_FILE_PATH = 'sent_emails' # change this to a proper location

# URL taht this site is hosted on
# Do not include the trailing slash.
SERVER_URL = 'http://www.rockitrecruit.com'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = '/srv/www/recruitmentmedia/'
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/srv/www/recruitmentstatic/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

#SOCIAL_AUTH_GOOGLE_WHITELISTED_DOMAINS = ['fivium.com', 'fivium.co.uk', 'fivium.com.au']

GOOGLE_ANALYTICS_TRACKING_ID = get_secret('GOOGLE_ANALYTICS_TRACKING_ID')
