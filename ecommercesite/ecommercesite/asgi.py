"""
ASGI config for ecommercesite project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Determinar el módulo de configuración según el entorno
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'ecommercesite.settings.production')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_asgi_application()
