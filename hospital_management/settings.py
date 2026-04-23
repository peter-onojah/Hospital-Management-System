import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-change-in-production'
DEBUG = True
ALLOWED_HOSTS = []

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Our apps (we'll add them one by one)
    'accounts',
    'hospital',
    'appointments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hospital_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'hospital_management.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# SMS Configuration (KudiSMS) - PRODUCTION READY
KUDISMS_API_KEY = 'WlToPkwDX5Ax4CIRcLUnMr9zif6VQSNv0hH1JgEyFYa2OZB3usjpGmK7bt8qed'
KUDISMS_SENDER_ID = 'FDN Hospt'  # Your sender ID
KUDISMS_API_URL = 'https://my.kudisms.net/user/apikey'  # ← CORRECT URL

# SMS Settings
SMS_TEST_MODE = False  # Set to False for production
SMS_REMINDER_ENABLED = True

# Add these for better debugging:
SMS_SIMULATION = False  # Set to False for real SMS

# SMS Message Templates
SMS_booking_REMINDER = "Dear {patient}, your booking for {department} at {time} on {date} is approved. Foundation Hospital."
SMS_booking_CONFIRMATION = "Dear {patient}, your booking with Dr. {doctor} on {date} at {time} has been confirmed. Please arrive 15 minutes early."
SMS_booking_CANCELLATION = "Dear {patient}, your booking with Dr. {doctor} on {date} has been cancelled. Contact reception for rescheduling."

SMS_COST_PER_MESSAGE = 5.95  # ₦5.95 per SMS
SMS_CURRENCY = 'NGN'
