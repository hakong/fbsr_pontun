import os
import os.path

# Grab settings from environment variables
HOSTNAME = os.environ.get('WEB_HOSTNAME', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
EMAIL_FROM = os.environ.get('EMAIL_FROM', '')

# Useful for development (when there is no reverse proxy in front)

LISTING_FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')
ADMIN_FRONTEND_FOLDER   = os.path.join(os.path.dirname(__file__), '..', 'admin',    'build')
DATABASE = {
    'database': os.environ.get('POSTGRES_DB', 'fbsr_pontun'),
    'user': os.environ.get('POSTGRES_USER', 'fbsr_pontun'),
    'host': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
    'password': os.environ.get('POSTGRES_PASSWORD', '')  # Defaulting to empty string if not set
}

TEMPLATE_VARS = {
    'account': os.environ.get('TEMPLATE_ACCOUNT', ''),
    'kt': os.environ.get('TEMPLATE_KT', ''),
    'receipt_email': os.environ.get('TEMPLATE_RECEIPT_EMAIL', '')
}

try:
    from .local_config import *
except ImportError:
    pass
