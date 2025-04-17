import os

# ...existing code...

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Static files configuration (asegúrate de que STATIC_URL y STATICFILES_DIRS estén configurados)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]