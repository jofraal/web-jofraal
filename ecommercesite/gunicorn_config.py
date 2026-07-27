# Configuración de Gunicorn para producción

import multiprocessing

# Configuración básica
bind = "0.0.0.0:8000"  # Dirección IP y puerto donde Gunicorn escuchará
workers = multiprocessing.cpu_count() * 2 + 1  # Número recomendado de workers
worker_class = "gthread"  # Tipo de worker (gthread es bueno para aplicaciones Django)
threads = 2  # Número de hilos por worker
timeout = 60  # Tiempo máximo en segundos para procesar una solicitud
keepalive = 5  # Tiempo en segundos para mantener conexiones abiertas

# Configuración de logs
accesslog = "-"  # Logs de acceso a stdout
errorlog = "-"  # Logs de error a stderr
loglevel = "info"  # Nivel de detalle de los logs

# Configuración de seguridad
forwarded_allow_ips = "*"  # Permitir X-Forwarded-For desde cualquier IP
secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}

# Configuración de rendimiento
max_requests = 1000  # Reiniciar workers después de procesar este número de solicitudes
max_requests_jitter = 50  # Añadir variación aleatoria para evitar que todos los workers se reinicien a la vez

# Configuración de Django
raw_env = ["DJANGO_SETTINGS_MODULE=ecommercesite.settings.production"]