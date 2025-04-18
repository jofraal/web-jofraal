"""
WSGI config for ecommercesite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Determinar el módulo de configuración según el entorno
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'ecommercesite.settings.production')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_wsgi_application()
