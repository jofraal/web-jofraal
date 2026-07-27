from .base import *
from decouple import config, Csv

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default='localhost,127.0.0.1')

# Dominio de producción para CSRF trusted origins
_DOMAIN = config('DOMAIN', default='')
CSRF_TRUSTED_ORIGINS = [
    f'https://{_DOMAIN}',
    f'https://www.{_DOMAIN}',
] if _DOMAIN else [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
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

# Seguridad en producción
SECURE_SSL_REDIRECT = True  # Redirigir todas las solicitudes HTTP a HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Para proxies inversos (nginx/Cloudflare)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# SAMEORIGIN permite iframes de MercadoPago checkout
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Política de seguridad de contenido (CSP)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:")

# Caché en producción (DatabaseCache para entornos sin Redis)
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
