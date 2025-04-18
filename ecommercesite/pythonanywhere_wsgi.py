# Este es un ejemplo de archivo WSGI para PythonAnywhere
# Deberás copiar este contenido en el archivo WSGI que PythonAnywhere te proporciona

import os
import sys
import dotenv

# Añadir la ruta del proyecto al path de Python
# Reemplaza 'tuusuario' con tu nombre de usuario de PythonAnywhere
path = '/home/tuusuario/ecommercesite'
if path not in sys.path:
    sys.path.append(path)

# Cargar variables de entorno desde el archivo .env
dotenv_path = os.path.join(path, '.env')
dotenv.load_dotenv(dotenv_path)

# Configurar el módulo de settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ecommercesite.settings.pythonanywhere'

# Importar la aplicación WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()