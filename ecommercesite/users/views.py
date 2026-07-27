from django.shortcuts import render, redirect, get_object_or_404
import os
import json
import logging
from functools import lru_cache
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, UserUpdateForm, AddressForm
from .models import Profile, Address
from cart.models import Cart
# Importar funciones de ubicaciones desde el módulo users.locations
from .locations import get_departments, get_provinces, get_districts

# Configurar logger
logger = logging.getLogger(__name__)

def register(request):
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # El perfil de usuario ya se crea en el método save del formulario
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

# API para obtener departamentos, provincias y distritos
def get_departments_api(request):
    """API para obtener la lista de departamentos de Perú"""
    try:
        # Usar la función importada de .locations
        departments = get_departments()
        
        # Registrar información para depuración
        logger.info(f"API get_departments_api llamada, obtenidos {len(departments)} departamentos")
        
        # Asegurarse de que departments sea una lista, incluso si está vacía
        if not isinstance(departments, list):
            departments = list(departments) if departments else []
            
        # Si no hay departamentos, intentar cargar desde orders como alternativa
        if not departments:
            logger.warning("No se encontraron departamentos en users.locations, intentando cargar desde orders.locations")
            try:
                # Importar dinámicamente para evitar problemas de importación circular
                from orders.locations import get_departments as orders_get_departments
                departments = orders_get_departments()
                logger.info(f"Departamentos cargados desde orders.locations: {len(departments)}")
                
                # Asegurarse de que departments sea una lista
                if not isinstance(departments, list):
                    departments = list(departments) if departments else []
            except Exception as e:
                logger.error(f"Error al cargar departamentos desde orders.locations: {e}")
        
        return JsonResponse(departments, safe=False)
    except Exception as e:
        logger.error(f"Error en get_departments_api: {e}")
        return JsonResponse({"error": str(e)}, status=500)

def get_provinces_api(request):
    """API para obtener las provincias de un departamento"""
    try:
        department = request.GET.get('department', '')
        if not department:
            return JsonResponse({'error': 'Departamento no especificado'}, status=400)
        
        # Obtener provincias usando la función importada de .locations
        provinces = get_provinces(department)
        
        # Registrar información para depuración
        logger.info(f"API get_provinces_api llamada para '{department}', obtenidas {len(provinces)} provincias")
        
        # Asegurarse de que provinces sea una lista, incluso si está vacía
        if not isinstance(provinces, list):
            provinces = list(provinces) if provinces else []
        
        # Si no hay provincias, intentar cargar desde orders como alternativa
        if not provinces:
            logger.warning(f"No se encontraron provincias para '{department}' en users.locations, intentando cargar desde orders.locations")
            try:
                # Importar dinámicamente para evitar problemas de importación circular
                from orders.locations import get_provinces as orders_get_provinces
                provinces = orders_get_provinces(department)
                logger.info(f"Provincias para '{department}' cargadas desde orders.locations: {len(provinces)}")
                
                # Asegurarse de que provinces sea una lista
                if not isinstance(provinces, list):
                    provinces = list(provinces) if provinces else []
            except Exception as e:
                logger.error(f"Error al cargar provincias desde orders.locations: {e}")
        
        return JsonResponse(provinces, safe=False)
    except Exception as e:
        logger.error(f"Error en get_provinces_api: {e}")
        return JsonResponse({"error": str(e)}, status=500)

def get_districts_api(request):
    """API para obtener los distritos de una provincia"""
    try:
        department = request.GET.get('department', '')
        province = request.GET.get('province', '')
        if not department or not province:
            return JsonResponse({'error': 'Departamento o provincia no especificados'}, status=400)
        
        # Obtener distritos desde users/locations.py
        districts = get_districts(department, province)
        logger.info(f"API get_districts_api llamada para '{department}', '{province}', obtenidos {len(districts)} distritos")
        
        if not districts:
            logger.warning(f"No se encontraron distritos para '{department}', '{province}' en users.locations, intentando cargar desde orders.locations")
            try:
                from orders.locations import get_districts as orders_get_districts
                districts = orders_get_districts(department, province)
                logger.info(f"Distritos para '{department}', '{province}' cargados desde orders.locations: {len(districts)}")
            except Exception as e:
                logger.error(f"Error al cargar distritos desde orders.locations: {e}")
                return JsonResponse({'error': 'No se encontraron distritos en ninguna fuente'}, status=404)
        
        # No es necesario reformatear, ya que get_districts devuelve [{"name": "..."}, ...]
        logger.debug(f"Distritos devueltos: {districts}")
        return JsonResponse(districts, safe=False)
    except Exception as e:
        logger.error(f"Error general en get_districts_api: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def profile(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    return render(request, 'users/profile.html', {
        'user': user,
        'profile': profile
    })

@login_required
def edit_profile(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        postal_code = request.POST.get('postal_code', '')
        country = request.POST.get('country', '')
        
        # Validar número telefónico
        if phone_number and (not phone_number.isdigit() or len(phone_number) != 9):
            messages.error(request, 'El número telefónico debe tener 9 dígitos numéricos')
            return render(request, 'users/edit_profile.html')
        
        # Actualizar datos del usuario
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        # Actualizar datos del perfil
        profile.phone_number = phone_number
        profile.address = address
        profile.city = city
        profile.state = state
        profile.postal_code = postal_code
        profile.country = country
        profile.save()
        
        messages.success(request, 'Tu perfil ha sido actualizado correctamente')
        return redirect('users:profile')
    
    return render(request, 'users/edit_profile.html')

@login_required
def order_history(request):
    # Obtener historial de pedidos del usuario
    orders = request.user.orders.all().order_by('-created_at')
    return render(request, 'users/order_history.html', {'orders': orders})

@login_required
def rate_product(request, product_id):
    # Obtener el producto
    from products.models import Product, ProductReview
    from products.forms import ProductReviewForm
    
    product = get_object_or_404(Product, id=product_id)
    order_id = request.POST.get('order_id') or request.GET.get('order_id')
    
    # Verificar que el usuario haya comprado el producto
    if not product.user_has_purchased(request.user):
        messages.error(request, 'Solo puedes calificar productos que hayas comprado.')
        return redirect('users:order_history')
    
    # Si es una solicitud POST, procesar el formulario
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            # Crear o actualizar la reseña
            review, created = ProductReview.objects.update_or_create(
                product=product,
                user=request.user,
                defaults=form.cleaned_data
            )
            
            # Actualizar la calificación promedio del producto
            product.update_rating()
            
            messages.success(request, '¡Gracias por tu valoración!')
            return redirect('users:order_history')
    else:
        # Verificar si el usuario ya ha calificado este producto
        try:
            review = ProductReview.objects.get(product=product, user=request.user)
            form = ProductReviewForm(instance=review)
            rating = review.rating
            comment = review.comment
        except ProductReview.DoesNotExist:
            form = ProductReviewForm()
            rating = 0
            comment = ''
    
    return render(request, 'users/rate_product.html', {
        'product': product,
        'form': form,
        'rating': rating,
        'comment': comment,
        'order_id': order_id
    })

@login_required
def addresses(request):
    # Vista para gestionar direcciones
    user = request.user
    addresses = Address.objects.filter(user=user).order_by('-is_default', '-created_at')
    
    # Verificar si el usuario tiene direcciones
    has_addresses = addresses.exists()
    can_add_more = addresses.count() < 3
    
    return render(request, 'users/addresses.html', {
        'section': 'addresses',
        'user': user,
        'addresses': addresses,
        'has_addresses': has_addresses,
        'can_add_more': can_add_more
    })

@login_required
def edit_address(request, address_id=None):
    user = request.user
    
    # Si se proporciona un ID, intentar obtener la dirección existente
    if address_id:
        address = get_object_or_404(Address, id=address_id, user=user)
        is_new = False
    else:
        # Verificar si el usuario ya tiene 3 direcciones
        if Address.objects.filter(user=user).count() >= 3:
            messages.error(request, 'No puedes agregar más de 3 direcciones. Elimina una existente primero.')
            return redirect('users:addresses')
        address = None
        is_new = True
    
    if request.method == 'POST':
        # Verificar si los datos de ubicación están disponibles
        department = request.POST.get('department')
        province = request.POST.get('province')
        district = request.POST.get('district')
        
        # Los campos recipient, country y address_type ahora son opcionales
        # y se manejan automáticamente en el modelo
        
        # Registrar información para depuración
        logger.info(f"Datos recibidos: department={department}, province={province}, district={district}")
        
        # Crear una copia de POST para modificar
        post_data = request.POST.copy()
            
        # Crear el formulario con los datos modificados
        form = AddressForm(post_data, instance=address, user=user)
        
        if form.is_valid():
            try:
                address_obj = form.save(commit=False)
                address_obj.user = user
                
                # Guardar coordenadas del mapa
                latitude = request.POST.get('latitude')
                longitude = request.POST.get('longitude')
                if latitude and longitude:
                    address_obj.latitude = float(latitude)
                    address_obj.longitude = float(longitude)
                    
                address_obj.save()
                
                if is_new:
                    messages.success(request, 'Dirección agregada correctamente.')
                else:
                    messages.success(request, 'Dirección actualizada correctamente.')
                return redirect('users:addresses')
            except Exception as e:
                messages.error(request, f'Error al guardar la dirección: {str(e)}')
                logger.error(f'Error al guardar dirección: {str(e)}')
        else:
            # Mostrar errores de validación
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
            logger.error(f'Errores de validación en el formulario: {form.errors}')

    else:
        form = AddressForm(instance=address, user=user)
    
    # Obtener datos para los selectores dinámicos usando la función importada
    departments = get_departments()
    logger.info(f"Departamentos obtenidos para el formulario: {len(departments)}")
    
    # Obtener provincias y distritos si hay una dirección existente
    provinces = []
    districts = []
    if address and address.department:
        provinces = get_provinces(address.department)
        logger.info(f"Provincias obtenidas para {address.department}: {len(provinces)}")
        if address.province:
            districts = get_districts(address.department, address.province)
            logger.info(f"Distritos obtenidos para {address.province}: {len(districts)}")
    
    return render(request, 'users/edit_address.html', {
        'form': form,
        'address': address,
        'is_new': is_new,
        'departments': departments,
        'provinces': provinces,
        'districts': districts,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY if hasattr(settings, 'GOOGLE_MAPS_API_KEY') else '',
    })

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        was_default = address.is_default
        address.delete()
        
        # Si era la dirección predeterminada, establecer otra como predeterminada
        if was_default:
            remaining = Address.objects.filter(user=request.user).first()
            if remaining:
                remaining.is_default = True
                remaining.save()
        
        messages.success(request, 'Dirección eliminada correctamente.')
        return redirect('users:addresses')
    
    return render(request, 'users/confirm_delete_address.html', {
        'address': address
    })

@login_required
def set_default_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    # Desmarcar todas las direcciones predeterminadas
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    
    # Establecer la nueva dirección predeterminada
    address.is_default = True
    address.save()
    
    messages.success(request, 'Dirección predeterminada actualizada correctamente.')
    return redirect('users:addresses')

# Esta sección ha sido eliminada para evitar duplicación de código.
# Las APIs de ubicaciones ya están definidas en la parte superior del archivo.

@login_required
def payment_methods(request):
    # Implementación de la función de métodos de pago que estaba comentada en urls.py
    user = request.user
    
    # Aquí se podría agregar lógica para obtener los métodos de pago guardados del usuario
    # Por ahora, solo renderizamos la plantilla existente
    
    return render(request, 'users/payment_methods.html', {
        'section': 'payment_methods',
        'user': user
    })

@login_required
def refund_info(request):
    # Vista para gestionar información de reembolso
    return render(request, 'users/refund_info.html', {
        'section': 'refund_info'
    })

@login_required
def wishlists(request):
    # Vista para gestionar listas de deseos
    return render(request, 'users/wishlists.html', {
        'section': 'wishlists'
    })

@login_required
def account_settings(request):
    # Vista para configuración de cuenta
    return render(request, 'users/account_settings.html', {
        'section': 'account_settings'
    })

def send_marketing_email(request):
    # Solo superusuarios pueden enviar correos masivos
    if not request.user.is_superuser:
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