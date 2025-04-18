from .base import *
import os
from decouple import config

DEBUG = False

# Configurar hosts permitidos - reemplazar con tu dominio de PythonAnywhere
ALLOWED_HOSTS = ['tuusuario.pythonanywhere.com']

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
X_FRAME_OPTIONS = 'DENY'

# Configuración de correo electrónico
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')