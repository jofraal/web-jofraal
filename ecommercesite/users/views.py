from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, UserUpdateForm
from .models import Profile
from cart.models import Cart

def register(request):
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear perfil de usuario
            Profile.objects.create(user=user)
            # Iniciar sesión automáticamente
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Registro exitoso. ¡Bienvenido!')
            return redirect('core:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        # Obtener datos con validación para evitar errores
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Validar que se proporcionaron los datos necesarios
        if not username_or_email or not password:
            return render(request, 'users/login.html', {
                'username_error': "Por favor, ingresa tu nombre de usuario o correo electrónico y contraseña."
            })

        # Bloqueo temporal por intentos fallidos con tiempo variable
        ip_address = request.META.get('REMOTE_ADDR', '')
        cache_key = f"login_attempts_{username_or_email}_{ip_address}"
        attempts = cache.get(cache_key, 0)
        
        # Tiempo de bloqueo exponencial basado en intentos
        if attempts >= 5:
            block_time = min(300 * (2 ** (attempts - 5)), 86400)  # Máximo 24 horas
            return render(request, 'users/login.html', {
                'username_error': f"Demasiados intentos fallidos. Intenta nuevamente más tarde.",
            })

        # Buscar usuario sin revelar información específica
        user = User.objects.filter(username=username_or_email).first() or \
               User.objects.filter(email=username_or_email).first()

        # Tiempo constante para verificación, independientemente de si el usuario existe
        authenticated_user = None
        if user:
            authenticated_user = authenticate(request, username=user.username, password=password)
        
        if authenticated_user:
            # Verificar si la cuenta está activa
            if not authenticated_user.is_active:
                return render(request, 'users/login.html', {
                    'username_error': "Esta cuenta ha sido desactivada. Contacta al administrador.",
                })
                
            # Inicio de sesión exitoso
            login(request, authenticated_user)
            cache.delete(cache_key)  # Restablecer intentos fallidos
            
            # Redirigir a la página solicitada o al perfil
            next_url = request.GET.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('users:profile')
        else:
            # Incrementar contador de intentos fallidos
            cache.incr(cache_key)
            cache.expire(cache_key, 3600)  # Mantener el contador por 1 hora
            
            # Mensaje genérico para no revelar información específica
            return render(request, 'users/login.html', {
                'password_error': "Credenciales incorrectas. Por favor, verifica e intenta nuevamente.",
            })

    return render(request, 'users/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('core:home')

@login_required
def profile(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente')
            return redirect('users:profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def order_history(request):
    # Obtener historial de pedidos del usuario
    orders = request.user.orders.all().order_by('-created')
    return render(request, 'users/order_history.html', {'orders': orders})

def send_marketing_email(request):
    # Verificar permisos - solo administradores pueden enviar correos masivos
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'No tienes permisos para realizar esta acción'}, status=403)
    
    subject = request.POST.get('subject', "Promoción especial")
    message = request.POST.get('message', "¡No te pierdas nuestras ofertas exclusivas!")
    from_email = settings.DEFAULT_FROM_EMAIL
    
    # Obtener destinatarios de la base de datos en lugar de hardcodearlos
    from core.models import NewsletterSubscriber
    subscribers = NewsletterSubscriber.objects.filter(active=True).values_list('email', flat=True)
    
    # Usar BCC para proteger la privacidad de los destinatarios
    try:
        # Enviar correos en lotes para evitar problemas con límites de servidores SMTP
        batch_size = 50  # Ajustar según los límites del servidor de correo
        total_subscribers = len(subscribers)
        
        for i in range(0, total_subscribers, batch_size):
            batch = list(subscribers[i:i+batch_size])
            if batch:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[from_email],  # Solo enviar al remitente como destinatario principal
                    bcc=batch,  # Usar BCC para los destinatarios reales
                    fail_silently=False,
                )
        
        return JsonResponse({'success': True, 'message': f'Correos enviados exitosamente a {total_subscribers} suscriptores.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al enviar correos: {e}'}, status=500)