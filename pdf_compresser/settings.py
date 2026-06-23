import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-pdf-compresser-secret-key-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'compressor',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pdf_compresser.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'pdf_compresser.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Max upload size: 2 GB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024 * 1024

# Ghostscript compression quality levels
GS_QUALITY_LEVELS = {
    'screen':  '/screen',    # 72 dpi — smallest file, web only
    'ebook':   '/ebook',     # 150 dpi — good balance
    'printer': '/printer',   # 300 dpi — high quality, less compression
    'prepress': '/prepress', # 300 dpi + color preservation, least compression
}

TARGET_SIZE_MB = 350
