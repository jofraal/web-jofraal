from .base import *

DEBUG = True
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'cb52-38-253-144-133.ngrok-free.app',  # Dominio específico de ngrok
    '*.ngrok-free.app',                    # Comodín para todos los subdominios de ngrok
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='3306'),
    }
}

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://ed4a-38-253-144-133.ngrok-free.app',
    'https://*.ngrok-free.app',
]

# Logging verboso en desarrollo
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}