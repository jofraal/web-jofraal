from .base import *
import os
from decouple import config

DEBUG = False

# Configurar hosts permitidos
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')], default='localhost,127.0.0.1')

# Dominio de producción para CSRF trusted origins
_DOMAIN = config('DOMAIN', default='')
CSRF_TRUSTED_ORIGINS = [
    f'https://{_DOMAIN}',
    f'https://www.{_DOMAIN}',
] if _DOMAIN else [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Configuración de base de datos MySQL para PythonAnywhere
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='tuusuario$ecommercesite'),
        'USER': config('DB_USER', default='tuusuario'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='tuusuario.mysql.pythonanywhere-services.com'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Configuración de archivos estáticos y media para PythonAnywhere
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')
MEDIA_URL = '/media/'

# Configuración de seguridad
SECURE_SSL_REDIRECT = False  # PythonAnywhere maneja esto a nivel de servidor
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Permite iframes de MercadoPago

# Caché en producción
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

# Deshabilitar debug en templates en producción
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.csrf',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'cart.context_processors.mercadopago_settings',
                'core.context_processors.google_maps_settings',
            ],
        },
    },
]

# Configuración de correo electrónico
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')