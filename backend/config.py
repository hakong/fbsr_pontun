import os
import os.path

# Fill out in local_config.py
HOSTNAME = ''
ADMIN_PASSWORD = '' 

SMTP_PASSWORD = ''
SMTP_SERVER = 'smtp.gmail.com'
EMAIL_FROM = ''

# Useful for development (when there is no reverse proxy in front)

LISTING_FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')
ADMIN_FRONTEND_FOLDER   = os.path.join(os.path.dirname(__file__), '..', 'admin',    'build')
DATABASE = dict(database='fbsr_pontun', user='fbsr_pontun', host='127.0.0.1')

REDIS = dict(host='localhost', db=1, port=6379)
REDIS_EMAIL_KEY = 'fbsr_pontun-email-queue'

TEMPLATE_VARS = {'account': '', 'kt': '', 'receipt_email': ''}

try:
    from .local_config import *
except ImportError:
    pass
