import os
from pathlib import Path

# Paths configuration (Three levels up from config/settings/ base structure)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security variables
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-grj=+x!)z88&&p9+-@%fvt-+74vwm3s&(4xbs%2&rpe^sarg54')

# Explicitly processes string definitions to prevent runtime evaluation crashes
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 't')

# Fallback structures explicitly protecting container runtimes
env_hosts = os.environ.get('ALLOWED_HOSTS', '')
if env_hosts:
    ALLOWED_HOSTS = env_hosts.split(',')
else:
    ALLOWED_HOSTS = ['*'] if DEBUG else ['localhost', '127.0.0.1', 'backend']

# Application definitions configuration
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Platform Middleware / Extensions
    'rest_framework',
    'corsheaders',
    
    'apps.users',
    'apps.banking',
    'apps.transactions',
    'apps.rewards',
    'apps.loans',
    'apps.assistant',
    'apps.memory',
    'apps.knowledge',
    'apps.audit',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database configuration mappings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'banking_ai'),
        'USER': os.environ.get('POSTGRES_USER', 'banking_ai'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'change_me'),
        'HOST': os.environ.get('POSTGRES_HOST', 'postgres'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
