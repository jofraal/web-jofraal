# Tienda Virtual - Guía de Despliegue

Este documento contiene las instrucciones para desplegar correctamente la aplicación de Tienda Virtual en un entorno de producción.

## Requisitos Previos

- Python 3.8 o superior
- MySQL o PostgreSQL
- Servidor web (Nginx o Apache)
- Cuenta en MercadoPago para procesamiento de pagos
- Claves de API para servicios externos (Google Maps, redes sociales, etc.)

## Pasos para el Despliegue

### 1. Configuración del Entorno

1. Clonar el repositorio en el servidor de producción
2. Crear un entorno virtual: `python -m venv venv`
3. Activar el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instalar dependencias: `pip install -r requirements.txt`

### 2. Configuración de Variables de Entorno

1. Copiar el archivo `.env.example` a `.env`
2. Editar el archivo `.env` con los valores reales para producción:
   - Configurar `DJANGO_SECRET_KEY` con una clave segura
   - Establecer `ALLOWED_HOSTS` con el dominio de producción
   - Configurar credenciales de base de datos
   - Añadir claves de API para MercadoPago, Google Maps, etc.
   - Configurar credenciales de correo electrónico

### 3. Configuración de la Base de Datos

1. Crear la base de datos en el servidor
2. Aplicar migraciones: `python manage.py migrate`
3. Crear superusuario: `python manage.py createsuperuser`
4. Cargar datos iniciales (si es necesario): `python manage.py loaddata fixtures/*.json`

### 4. Archivos Estáticos y Media

1. Recopilar archivos estáticos: `python manage.py collectstatic --no-input`
2. Configurar el servidor web para servir archivos estáticos y media

### 5. Configuración del Servidor Web

#### Usando Gunicorn

1. Iniciar Gunicorn con la configuración proporcionada:
   ```
   gunicorn --config=gunicorn_config.py ecommercesite.wsgi:application
   ```

#### Configuración de Nginx (ejemplo)

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Redireccionar HTTP a HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name tu-dominio.com www.tu-dominio.com;

    ssl_certificate /ruta/a/certificado.pem;
    ssl_certificate_key /ruta/a/clave-privada.pem;

    # Configuración SSL recomendada
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';

    # Archivos estáticos
    location /static/ {
        alias /ruta/a/tu/proyecto/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # Archivos media
    location /media/ {
        alias /ruta/a/tu/proyecto/mediafiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # Proxy para Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. Seguridad Adicional

1. Configurar un firewall (UFW en Ubuntu)
2. Configurar certificados SSL (Let's Encrypt)
3. Configurar copias de seguridad automáticas

### 7. Monitoreo

1. Configurar logs de aplicación
2. Implementar monitoreo de servidor (opcional)

## Verificación del Despliegue

1. Verificar que el sitio sea accesible a través de HTTPS
2. Probar el proceso de registro y login
3. Verificar el funcionamiento del carrito de compras
4. Realizar una compra de prueba con MercadoPago en modo sandbox
5. Verificar el envío de correos electrónicos

## Solución de Problemas Comunes

- **Error 500**: Verificar los logs de la aplicación y del servidor web
- **Problemas con archivos estáticos**: Verificar la configuración de STATIC_ROOT y MEDIA_ROOT
- **Problemas con MercadoPago**: Verificar las credenciales y la configuración de webhook
- **Problemas de correo electrónico**: Verificar la configuración SMTP y las credenciales

## Mantenimiento

1. Actualizar regularmente las dependencias
2. Monitorear el uso de recursos del servidor
3. Realizar copias de seguridad periódicas de la base de datos