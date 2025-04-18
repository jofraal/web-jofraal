# Guía de Despliegue en PythonAnywhere

Esta guía te ayudará a desplegar tu tienda virtual Django en PythonAnywhere paso a paso.

## 1. Crear una cuenta en PythonAnywhere

1. Ve a [PythonAnywhere](https://www.pythonanywhere.com/) y regístrate para obtener una cuenta.
2. Para proyectos comerciales, considera un plan pago que ofrezca más recursos y la posibilidad de usar tu propio dominio.

## 2. Configurar el entorno en PythonAnywhere

### 2.1 Crear una aplicación web

1. Una vez que hayas iniciado sesión, ve al panel de control.
2. Haz clic en la pestaña "Web" y luego en "Add a new web app".
3. Selecciona "Manual configuration" (no "Django").
4. Selecciona Python 3.9 o la versión más reciente disponible.

### 2.2 Configurar un entorno virtual

1. Ve a la pestaña "Consoles" y abre una nueva consola Bash.
2. Crea un entorno virtual con el siguiente comando:

```bash
mkvirtualenv --python=/usr/bin/python3.9 ecommercesite-env
```

3. El entorno virtual se activará automáticamente. Si necesitas activarlo más tarde, usa:

```bash
workon ecommercesite-env
```

## 3. Subir el código del proyecto

### 3.1 Usando Git (recomendado)

1. Si tu proyecto está en un repositorio Git, puedes clonarlo directamente:

```bash
cd ~
git clone https://github.com/tu-usuario/tu-repositorio.git ecommercesite
```

### 3.2 Usando el Uploader de archivos

1. Comprime tu proyecto en un archivo ZIP.
2. Ve a la pestaña "Files" en PythonAnywhere.
3. Sube el archivo ZIP y descomprímelo:

```bash
unzip tu-archivo.zip -d ecommercesite
```

## 4. Instalar dependencias

1. Asegúrate de que tu entorno virtual esté activado.
2. Navega a la carpeta de tu proyecto e instala las dependencias:

```bash
cd ~/ecommercesite
pip install -r requirements.txt
```

## 5. Configurar la base de datos MySQL

1. Ve a la pestaña "Databases" en PythonAnywhere.
2. Crea una nueva base de datos MySQL.
3. Anota el nombre de usuario, contraseña y nombre de la base de datos.

## 6. Configurar variables de entorno

1. Crea un archivo `.env` en la raíz de tu proyecto con las siguientes variables:

```
DJANGO_SECRET_KEY=tu_clave_secreta
DJANGO_SETTINGS_MODULE=ecommercesite.settings.pythonanywhere
DB_NAME=tuusuario$ecommercesite
DB_USER=tuusuario
DB_PASSWORD=tu_contraseña_mysql
DB_HOST=tuusuario.mysql.pythonanywhere-services.com
DB_PORT=3306
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_de_app
DEFAULT_FROM_EMAIL=tu_correo@gmail.com
MERCADO_PAGO_ACCESS_TOKEN=tu_token_de_acceso
MERCADO_PAGO_PUBLIC_KEY=tu_clave_publica
```

2. Reemplaza los valores con tus propias credenciales.

## 7. Configurar el archivo WSGI

1. Ve a la pestaña "Web" y busca la sección "Code" donde aparece el enlace al archivo WSGI.
2. Haz clic en el enlace para editar el archivo WSGI.
3. Reemplaza todo el contenido con lo siguiente:

```python
import os
import sys
import dotenv

# Añadir la ruta del proyecto al path de Python
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
```

4. Reemplaza `tuusuario` con tu nombre de usuario de PythonAnywhere.

## 8. Configurar archivos estáticos

1. Ve a la pestaña "Web" y busca la sección "Static files".
2. Añade las siguientes configuraciones:
   - URL: `/static/`
   - Directory: `/home/tuusuario/ecommercesite/staticfiles`
   - URL: `/media/`
   - Directory: `/home/tuusuario/ecommercesite/mediafiles`

## 9. Recolectar archivos estáticos y migrar la base de datos

1. Abre una consola Bash y activa tu entorno virtual.
2. Navega a la carpeta de tu proyecto y ejecuta:

```bash
cd ~/ecommercesite
python manage.py collectstatic --noinput
python manage.py migrate
```

## 10. Crear un superusuario (opcional)

```bash
python manage.py createsuperuser
```

## 11. Reiniciar la aplicación web

1. Ve a la pestaña "Web" y haz clic en el botón "Reload" para reiniciar tu aplicación.

## 12. Instalar python-decouple y python-dotenv

Asegúrate de que estas dependencias estén instaladas en tu entorno virtual:

```bash
pip install python-decouple python-dotenv
```

## 13. Verificar el despliegue

1. Tu sitio debería estar disponible en `https://tuusuario.pythonanywhere.com`
2. Verifica que puedas acceder al panel de administración en `https://tuusuario.pythonanywhere.com/admin/`

## Solución de problemas

### Errores comunes

1. **Error 500**: Verifica los logs de error en la pestaña "Web" > "Logs".
2. **Archivos estáticos no se cargan**: Asegúrate de haber ejecutado `collectstatic` y configurado correctamente las rutas de archivos estáticos.
3. **Problemas de base de datos**: Verifica la configuración de la base de datos y asegúrate de haber ejecutado las migraciones.

### Logs

Para ver los logs de error, ve a la pestaña "Web" y haz clic en los enlaces de logs:
- Error log
- Server log
- Access log

## Actualizar el sitio

Cuando necesites actualizar tu sitio:

1. Sube los cambios a PythonAnywhere (usando Git o el uploader).
2. Ejecuta las migraciones si has cambiado modelos.
3. Recolecta los archivos estáticos si has añadido o modificado archivos estáticos.
4. Reinicia la aplicación web desde la pestaña "Web".

---

¡Felicidades! Tu tienda virtual ahora debería estar funcionando en PythonAnywhere.