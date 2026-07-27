from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponse

class AdminLoginRateLimitMiddleware:
    """
    Protege el login del admin contra ataques de fuerza bruta.
    - 5 intentos fallidos por IP en 60 segundos → bloqueo de 15 minutos.
    - Detecta éxito (redirect 302) vs fallo (render 200) del login.
    """

    ADMIN_LOGIN_PATH = '/panel-control/login/'
    MAX_ATTEMPTS = 5
    WINDOW_SECONDS = 60
    BLOCK_SECONDS = 900  # 15 minutos

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == self.ADMIN_LOGIN_PATH:
            ip = self._get_client_ip(request)
            block_key = f'admin_brute_block_{ip}'

            if cache.get(block_key):
                return HttpResponse(
                    'Demasiados intentos de inicio de sesión. '
                    'Inténtalo de nuevo en 15 minutos.',
                    status=429,
                )

        response = self.get_response(request)

        if request.path == self.ADMIN_LOGIN_PATH and request.method == 'POST':
            ip = self._get_client_ip(request)
            attempt_key = f'admin_login_attempts_{ip}'
            block_key = f'admin_brute_block_{ip}'

            if response.status_code == 302:
                cache.delete(attempt_key)
            else:
                attempts = cache.get(attempt_key, 0) + 1
                if attempts >= self.MAX_ATTEMPTS:
                    cache.set(block_key, True, self.BLOCK_SECONDS)
                    cache.delete(attempt_key)
                else:
                    cache.set(attempt_key, attempts, self.WINDOW_SECONDS)

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class AdminAccessMiddleware:
    """Middleware to restrict access to the Django admin interface to staff members only."""

    # Rutas del admin que deben ser accesibles sin ser superuser (login, static)
    ALLOWED_PATHS = ['/panel-control/login/', '/panel-control/jsi18n/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/panel-control/'):
            # Permitir acceso a la página de login y recursos estáticos del admin
            for allowed in self.ALLOWED_PATHS:
                if request.path.startswith(allowed):
                    return self.get_response(request)
            if not request.user.is_superuser:
                return redirect('users:login')
        return self.get_response(request)