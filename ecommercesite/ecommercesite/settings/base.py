import os
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')

# Security keys Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN = config('MERCADO_PAGO_ACCESS_TOKEN')
MERCADO_PAGO_PUBLIC_KEY = config('MERCADO_PAGO_PUBLIC_KEY')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Aplicaciones locales
    'core',
    'products',  # Asegúrate de que esta línea esté presente
    'cart',
    'orders',
    'users',
    'coupons', # Añadir la aplicación de cupones
    # Aplicaciones de terceros
    'social_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',  # Middleware para manejar errores de autenticación social
    'users.middleware.AdminAccessMiddleware',  # Middleware para restringir acceso al admin
]

ROOT_URLCONF = 'ecommercesite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',  # Agregado para autenticación social
                'social_django.context_processors.login_redirect',  # Agregado para redirecciones
                'cart.context_processors.mercadopago_settings',  # Agregado para configuraciones de Mercado Pago
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommercesite.wsgi.application'

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',    # Backend para Google
    'social_core.backends.facebook.FacebookOAuth2', # Backend para Facebook
    'social_core.backends.linkedin.LinkedinOAuth2', # Backend para LinkedIn
    'social_core.backends.apple.AppleIdAuth',      # Backend para Apple
    'django.contrib.auth.backends.ModelBackend',    # Backend por defecto de Django
]

AUTH_PASSWORD_VALIDATORS = [
    # ...existing code...
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de correo electrónico
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Backend SMTP de Django
EMAIL_HOST = 'smtp.gmail.com'  # Servidor SMTP de Gmail
EMAIL_PORT = 587  # Puerto estándar para TLS
EMAIL_USE_TLS = True  # Habilita TLS para conexiones seguras
EMAIL_HOST_USER = config('EMAIL_HOST_USER')  # Tu correo de Gmail
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  # Contraseña de aplicación de Gmail
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')  # Correo que aparecerá como remitente

# Configuración adicional para solucionar problemas de envío de correo
EMAIL_TIMEOUT = 30  # Tiempo de espera en segundos para conexiones SMTP
EMAIL_USE_SSL = False  # No usar SSL (ya estamos usando TLS)

# Configuración adicional
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

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

# Seguridad de cookies
SESSION_COOKIE_SECURE = True  # Solo enviar cookies de sesión a través de HTTPS
SESSION_COOKIE_HTTPONLY = True  # Evitar acceso a cookies desde JavaScript
CSRF_COOKIE_SECURE = True  # Solo enviar cookies CSRF a través de HTTPS
CSRF_COOKIE_HTTPONLY = True  # Evitar acceso a cookies CSRF desde JavaScript

# Configuración de expiración de sesiones
SESSION_COOKIE_AGE = 3600  # Expiración de sesión después de 1 hora (en segundos)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # La sesión expira al cerrar el navegador
SESSION_SAVE_EVERY_REQUEST = True  # Actualizar la cookie de sesión en cada solicitud

# Rotación de tokens CSRF
CSRF_COOKIE_AGE = 10800  # Expiración del token CSRF después de 3 horas (en segundos)
CSRF_USE_SESSIONS = True  # Almacenar tokens CSRF en la sesión para mayor seguridad
CSRF_TRUSTED_ORIGINS = []  # Orígenes confiables para solicitudes CSRF

# Encabezados de seguridad
SECURE_BROWSER_XSS_FILTER = True  # Habilitar filtro XSS en navegadores
SECURE_CONTENT_TYPE_NOSNIFF = True  # Evitar que el navegador interprete tipos MIME incorrectos
X_FRAME_OPTIONS = 'DENY'  # Prevenir ataques de clickjacking

# Política de seguridad de contenido (CSP)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:")

# Configuración adicional para HSTS
SECURE_HSTS_SECONDS = 31536000  # Habilitar HSTS por un año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Claves de APIs para autenticación social
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', default='')

# URL de redirección autorizada para Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = config('SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI')

# Configuración de Facebook
SOCIAL_AUTH_FACEBOOK_KEY = config('SOCIAL_AUTH_FACEBOOK_KEY', default='')
SOCIAL_AUTH_FACEBOOK_SECRET = config('SOCIAL_AUTH_FACEBOOK_SECRET', default='')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']  # Permisos adicionales
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'id, name, email'}

# Configuración de LinkedIn
SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = config('SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY', default='')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = config('SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET', default='')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ['r_liteprofile', 'r_emailaddress']
SOCIAL_AUTH_LINKEDIN_OAUTH2_FIELD_SELECTORS = ['emailAddress', 'firstName', 'lastName']

# Configuración de URL para social auth
SOCIAL_AUTH_URL_NAMESPACE = 'social_auth'

# Redirecciones después de login/logout
LOGIN_URL = '/users/login/'  # URL de inicio de sesión
LOGIN_REDIRECT_URL = '/users/profile/'  # A dónde redirigir tras login exitoso
LOGOUT_REDIRECT_URL = '/'  # A dónde redirigir tras logout
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/users/profile/'  # Redirección tras login social
SOCIAL_AUTH_LOGIN_ERROR_URL = '/users/login/'  # Redirección en caso de error

# Esta configuración ya está definida arriba, eliminando duplicación

# Configuración de URL para inicio de sesión
LOGIN_URL = '/users/login/'  # Asegúrate de que esta URL coincida con la vista de inicio de sesión configurada

# Redirection after login
LOGIN_REDIRECT_URL = '/users/profile/'  # Redirect to the user's profile page after login