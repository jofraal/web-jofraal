from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Prefetch
from cart.models import Cart, CartItem
from cart.views import get_or_create_cart
from .forms import OrderCreateForm, OrderIdentificationForm, OrderShippingForm
from .models import OrderItem, Order
from django.contrib import messages
from decimal import Decimal
import mercadopago
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
from django.http import JsonResponse
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from .locations import PERU_LOCATIONS, get_provinces, get_districts as get_district_list, get_departments
from users.models import Profile, Address
from users.forms import AddressForm
import time
import uuid

logger = logging.getLogger(__name__)

# Vistas API para manejar las solicitudes AJAX de ubicaciones
def get_departments_api(request):
    """Vista API para obtener la lista de departamentos"""
    departments = get_departments()
    if not isinstance(departments, list):
        departments = list(departments) if departments else []
    return JsonResponse(departments, safe=False)

def get_provinces_api(request):
    """Vista API para obtener las provincias de un departamento"""
    department = request.GET.get('department', '')
    if not department:
        return JsonResponse({'error': 'Departamento no especificado'}, status=400)
    
    provinces = get_provinces(department)
    if not isinstance(provinces, list):
        provinces = list(provinces) if provinces else []
    return JsonResponse(provinces, safe=False)

def get_districts_api(request):
    """Vista API para obtener los distritos de una provincia"""
    department = request.GET.get('department', '')
    province = request.GET.get('province', '')
    if not department or not province:
        return JsonResponse({'error': 'Departamento o provincia no especificados'}, status=400)
    
    districts = get_district_list(department, province)
    if not isinstance(districts, list):
        districts = list(districts) if districts else []
    return JsonResponse(districts, safe=False)

@login_required
def get_user_data_api(request):
    """Vista API para obtener los datos personales del usuario autenticado"""
    user = request.user
    
    profile, created = Profile.objects.get_or_create(user=user)
    
    user_data = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': profile.phone_number,
        'document_type': profile.document_type,
        'document_number': profile.document_number
    }
    
    return JsonResponse(user_data)

@login_required
def get_user_addresses_api(request):
    """Vista API para obtener las direcciones guardadas del usuario autenticado"""
    user = request.user
    
    addresses = Address.objects.filter(user=user).order_by('-is_default', '-created_at')    
    
    seen = set()
    unique_addresses = []
    for address in addresses:
        key = (
            address.department,
            address.province,
            address.district,
            address.street,
            address.street_number,
            address.additional_info
        )
        if key not in seen:
            seen.add(key)
            unique_addresses.append(address)
            
    addresses_data = []
    for address in unique_addresses:
        addresses_data.append({
            'id': address.id,
            'address_type': address.address_type,
            'address_type_display': address.get_address_type_display(),
            'department': address.department,
            'province': address.province,
            'district': address.district,
            'street': address.street,
            'street_number': address.street_number,
            'additional_info': address.additional_info,
            'recipient': address.recipient,
            'country': address.country,
            'is_default': address.is_default,
            'address': address.address,
            'city': address.city,
            'state': address.state
        })
    
    if not addresses_data:
        return JsonResponse({'error': 'No se encontraron direcciones guardadas'}, status=404)
    
    return JsonResponse(addresses_data, safe=False)

def delivery_form(request):
    return redirect('orders:checkout')

@require_POST
@never_cache
def save_session_data(request):
    """Guarda los datos de identificación y envío en la sesión del servidor, evitando duplicidad."""
    try:
        data = json.loads(request.body)
        # Solo guardar si no existen o si hay cambios
        if 'identification_data' in data:
            if request.session.get('identification_data') != data['identification_data']:
                request.session['identification_data'] = data['identification_data']
                logger.info(f"Datos de identificación guardados en sesión: {data['identification_data']}")
        if 'shipping_data' in data:
            if request.session.get('shipping_data') != data['shipping_data']:
                request.session['shipping_data'] = data['shipping_data']
                logger.info(f"Datos de envío guardados en sesión: {data['shipping_data']}")
        request.session.modified = True
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON en save_session_data: {e}")
        return JsonResponse({'error': 'Formato de datos inválido', 'detalle': str(e)}, status=400)
    except Exception as e:
        logger.exception(f"Error inesperado en save_session_data: {e}")
        return JsonResponse({'error': 'Error inesperado al guardar datos de sesión', 'detalle': str(e)}, status=500)

@require_POST
@never_cache
def create_payment(request):
    logger.info("Iniciando create_payment")
    try:
        if not hasattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN') or not settings.MERCADO_PAGO_ACCESS_TOKEN:
            logger.error("Token de MercadoPago no configurado")
            return JsonResponse({"error": "Error de configuración del sistema de pagos. Contacte al administrador."}, status=500)
        identification_data = request.session.get('identification_data', {})
        shipping_data = request.session.get('shipping_data', {})
        logger.debug(f"identification_data: {identification_data}")
        logger.debug(f"shipping_data: {shipping_data}")
        logger.debug(f"document_type: {identification_data.get('document_type', 'N/A')}")
        logger.debug(f"document_number: {identification_data.get('document_number', 'N/A')}")
        if not identification_data or not shipping_data:
            logger.error("Datos de checkout incompletos")
            return JsonResponse({"error": "Por favor complete todos los pasos del proceso de compra."}, status=400)
        # Validar campos mínimos de identificación
        for campo in ['first_name', 'last_name', 'email', 'phone']:
            if not identification_data.get(campo):
                logger.error(f"Falta el campo obligatorio: {campo}")
                return JsonResponse({"error": f"Falta el campo obligatorio: {campo}"}, status=400)
        # Validar campos mínimos de envío
        for campo in ['department', 'province', 'district']:
            if not shipping_data.get(campo):
                logger.error(f"Falta el campo de envío obligatorio: {campo}")
                return JsonResponse({"error": f"Falta el campo de envío obligatorio: {campo}"}, status=400)
        # Combinar datos con valores por defecto
        defaults = {
            'first_name': 'Cliente',
            'last_name': 'Tienda Virtual',
            'email': 'cliente@ejemplo.com',
            'phone': '123456789',
            'city': shipping_data.get('district', 'Lima'),
            'address': 'Pendiente',
            'department': shipping_data.get('department', 'Lima'),
            'province': shipping_data.get('province', 'Lima'),
            'district': shipping_data.get('district', 'Lima'),
            'street': shipping_data.get('street', ''),
            'street_number': shipping_data.get('street_number', ''),
            'additional_info': shipping_data.get('additional_info', ''),
            'country': 'PE'
        }
        # Construir dirección real
        direccion_partes = []
        if shipping_data.get('street'):
            direccion_partes.append(str(shipping_data.get('street')))
        if shipping_data.get('street_number'):
            direccion_partes.append(str(shipping_data.get('street_number')))
        if shipping_data.get('district'):
            direccion_partes.append(str(shipping_data.get('district')))
        if shipping_data.get('province'):
            direccion_partes.append(str(shipping_data.get('province')))
        if shipping_data.get('department'):
            direccion_partes.append(str(shipping_data.get('department')))
        direccion = ', '.join([p for p in direccion_partes if p])
        if not direccion:
            direccion = 'Sin dirección'
        # Redondear lat/lon
        lat = shipping_data.get('latitude')
        lon = shipping_data.get('longitude')
        try:
            lat = round(float(lat), 7) if lat is not None and lat != '' else None
            logger.debug(f"Latitud procesada en create_payment: {lat}")
        except Exception as e:
            logger.error(f"Error al procesar latitud en create_payment: {e}")
            lat = None
        try:
            lon = round(float(lon), 7) if lon is not None and lon != '' else None
            logger.debug(f"Longitud procesada en create_payment: {lon}")
        except Exception as e:
            logger.error(f"Error al procesar longitud en create_payment: {e}")
            lon = None
        
        # Actualizar los datos de envío con las coordenadas procesadas
        shipping_data['latitude'] = lat
        shipping_data['longitude'] = lon
        # Combinar los datos de identificación y envío
        order_data = {**defaults, **identification_data, **shipping_data}
        order_data['address'] = direccion
        order_data['city'] = shipping_data.get('district', 'Lima')
        order_data['country'] = 'PE'
        # Asegurar que los datos de documento estén presentes
        order_data['document_type'] = identification_data.get('document_type', '')
        order_data['document_number'] = identification_data.get('document_number', '')
        # Validar latitud y longitud si existen y redondear a 16 decimales o menos
        latitude = shipping_data.get('latitude')
        longitude = shipping_data.get('longitude')
        if latitude is not None and latitude != '':
            try:
                # Convertir a Decimal y limitar a 16 decimales para evitar errores de validación
                from decimal import Decimal
                order_data['latitude'] = Decimal(str(float(latitude))).quantize(Decimal('0.0000000000000001'))
                logger.debug(f"Latitud procesada correctamente: {order_data['latitude']}")
            except Exception as e:
                logger.error(f"Error al procesar latitud {latitude}: {e}")
                order_data['latitude'] = None
        if longitude is not None and longitude != '':
            try:
                # Convertir a Decimal y limitar a 16 decimales para evitar errores de validación
                from decimal import Decimal
                order_data['longitude'] = Decimal(str(float(longitude))).quantize(Decimal('0.0000000000000001'))
                logger.debug(f"Longitud procesada correctamente: {order_data['longitude']}")
            except Exception as e:
                logger.error(f"Error al procesar longitud {longitude}: {e}")
                order_data['longitude'] = None
        logger.debug(f"Datos combinados para la orden: {order_data}")
        cart = get_or_create_cart(request)
        selected_items = cart.items.filter(selected=True).select_related('product', 'variant')
        if not selected_items.exists():
            logger.error("No hay productos seleccionados")
            return JsonResponse({'error': 'No hay productos seleccionados'}, status=400)
        # Definir shipping_cost a partir del carrito
        shipping_cost = getattr(cart, 'shipping_cost', 0) or 0
        try:
            total_cost = cart.get_final_total()
        except Exception as e:
            logger.error(f"Error al obtener el total del carrito: {e}")
            return JsonResponse({"error": "Error al calcular el total del carrito."}, status=500)
        try:
            from decimal import Decimal
            coupon_discount = Decimal(str(cart.get_coupon_discount_amount() or 0)).quantize(Decimal('0.01'))
        except Exception as e:
            logger.error(f"Error al obtener el descuento de cupón: {e}")
            from decimal import Decimal
            coupon_discount = Decimal('0')
        if total_cost <= 0:
            logger.error("El monto total de la transacción es cero o negativo")
            return JsonResponse({"error": "El monto total de la transacción no puede ser cero o negativo"}, status=400)
        try:
            from .utils import create_order_from_cart
            order = create_order_from_cart(cart, order_data)
            # Orden creada exitosamente
            logger.info(f"Orden creada exitosamente: {order.id}")
            # Limpiar carrito y datos de sesión tras crear la orden
            if 'cart_id' in request.session:
                del request.session['cart_id']
            if 'identification_data' in request.session:
                del request.session['identification_data']
            if 'shipping_data' in request.session:
                del request.session['shipping_data']
            request.session.modified = True
        except Exception as e:
            logger.error(f"Error al crear la orden de compra: {e}")
            return JsonResponse({"error": "No se pudo crear la orden de compra. Intente nuevamente."}, status=500)
        # Aquí continúa el flujo normal de creación de preferencia de Mercado Pago...
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        items = []
        for item in selected_items:
            quantity = item.quantity
            try:
                if hasattr(item, 'total_price') and callable(item.total_price):
                    unit_price = float(item.total_price()) / quantity if quantity > 0 else float(item.product.price)
                elif hasattr(item.product, 'price'):
                    unit_price = float(item.product.price)
                else:
                    unit_price = 0.01
            except Exception as e:
                logger.error(f"Error al calcular el precio unitario: {e}")
                unit_price = 0.01
            items.append({
                "title": str(item.product),
                "quantity": quantity,
                "unit_price": round(unit_price, 2),
                "currency_id": "PEN",
                "description": str(item.variant) if item.variant else "",
                "picture_url": item.product.image.url if hasattr(item.product, 'image') and item.product.image else ""
            })
        if not items:
            logger.error("No hay productos seleccionados para el pago")
            return JsonResponse({"error": "No hay productos seleccionados"}, status=400)
        success_url = request.build_absolute_uri('/orders/success/')
        failure_url = request.build_absolute_uri('/orders/failure/')
        pending_url = request.build_absolute_uri('/orders/pending/')
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        preference_data = {
            "items": [
                {
                    "title": "Pedido en Tienda Virtual",
                    "quantity": 1,
                    "unit_price": float(cart.get_final_total()),
                    "currency_id": "PEN",
                }
            ],
            "payer": {
                "email": order_data["email"],
                "name": order_data["first_name"],
                "surname": order_data["last_name"],
                "phone": {
                    "area_code": "51",
                    "number": order_data["phone"]
                },
                "address": {
                    "zip_code": "",
                    "street_name": order_data["street"],
                    "street_number": order_data["street_number"]
                }
            },
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url,
            },
            "external_reference": f"{order_data['email']}_{int(time.time())}_{order.id}",
        }
        try:
            preference_response = sdk.preference().create(preference_data)
            logger.debug(f"Respuesta de MercadoPago (status): {preference_response.get('status')}")
            
            # Verificar si la API de MercadoPago devolvió un error
            status_code = preference_response.get("status")
            if status_code and status_code >= 400:
                error_detail = preference_response.get("response", {})
                error_msg = error_detail.get("message", "Error desconocido de MercadoPago")
                logger.error(f"MercadoPago API error (status={status_code}): {error_msg} - Detalle: {error_detail}")
                return JsonResponse({
                    "error": f"Error de MercadoPago: {error_msg}",
                    "detalle": str(error_detail)
                }, status=500)
            
            preference = preference_response.get("response", {})
            
            # Guardar el ID de preferencia en la orden
            if "id" in preference:
                preference_id = preference["id"]
                order.payment_preference_id = preference_id
                order.external_reference = f"{order_data['email']}_{int(time.time())}_{order.id}"
                order.request_token = str(uuid.uuid4())  # Generar un token único
                order.save()
                logger.info(f"Orden actualizada con preference_id={preference_id}")
                
                # Guardar datos en la sesión para recuperarlos en las vistas de éxito/fallo
                request.session['preference_id'] = preference_id
                request.session['order_id'] = order.id
                request.session.modified = True
            
            if "init_point" in preference:
                logger.info(f"init_point generado: {preference['init_point']}")
                return JsonResponse({"init_point": preference["init_point"]})
            elif "id" in preference:
                logger.warning(f"Preferencia generada sin init_point, solo id: {preference['id']}")
                return JsonResponse({"preference_id": preference["id"]})
            else:
                logger.error(f"Respuesta de preferencia sin init_point ni id: {preference}")
                return JsonResponse({"error": "No se pudo generar el enlace de pago.", "detalle": str(preference)}, status=500)
        except Exception as e:
            logger.exception(f"Error al crear preferencia de pago: {e}")
            return JsonResponse({"error": "Error al procesar el pago. Intente nuevamente.", "detalle": str(e)}, status=500)
    except Exception as e:
        logger.exception(f"Error inesperado en create_payment: {e}")
        # Mejorar el mensaje de error para el frontend y evitar error 500 genérico
        return JsonResponse({"error": "Ocurrió un error inesperado al procesar el pago. Por favor, intente nuevamente o contacte soporte si el problema persiste.", "detalle": str(e)}, status=500)

@never_cache
def checkout(request):
    cart = get_or_create_cart(request)
    selected_items = cart.items.filter(selected=True).select_related('product', 'variant')
    total = cart.get_final_total()
    coupon = cart.coupon
    discount_amount = cart.get_coupon_discount_amount()

    if not selected_items.exists():
        messages.warning(request, "Tu carrito está vacío o no has seleccionado productos.")
        return redirect('cart:cart_detail')

    identification_data = request.session.get('identification_data', {})
    shipping_data = request.session.get('shipping_data', {})

    identification_form = OrderIdentificationForm(initial=identification_data)
    shipping_form = OrderShippingForm(initial=shipping_data)

    context = {
        'identification_form': identification_form,
        'shipping_form': shipping_form,
        'selected_items': selected_items,
        'total': total,
        'coupon': coupon,
        'discount_amount': discount_amount,
        'cart': cart,
        'mercadopago_public_key': settings.MERCADO_PAGO_PUBLIC_KEY,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'breadcrumbs': [{'label': 'Carrito', 'url': None}, {'label': 'Checkout', 'url': None}],
    }
    return render(request, 'orders/multi_step_checkout.html', context)

@require_POST
@never_cache
def save_identification(request):
    try:
        data = json.loads(request.body)
        identification_form = OrderIdentificationForm(data)
        if identification_form.is_valid():
            cleaned_data = identification_form.cleaned_data
            
            # Log específico para verificar los campos de documento antes de guardar
            logger.info(f"document_type en cleaned_data: {cleaned_data.get('document_type', 'NO ENCONTRADO')}")
            logger.info(f"document_number en cleaned_data: {cleaned_data.get('document_number', 'NO ENCONTRADO')}")
            logger.info(f"Todas las claves en cleaned_data: {list(cleaned_data.keys())}")
            
            # Solo guardar si hay cambios respecto a la sesión
            if request.session.get('identification_data') != cleaned_data:
                request.session['identification_data'] = cleaned_data
                request.session.modified = True
                logger.info(f"Datos de identificación guardados: {cleaned_data}")
                
                # Verificar que se guardaron correctamente en la sesión
                saved_data = request.session.get('identification_data', {})
                logger.info(f"Verificación - document_type guardado en sesión: {saved_data.get('document_type', 'NO ENCONTRADO')}")
                logger.info(f"Verificación - document_number guardado en sesión: {saved_data.get('document_number', 'NO ENCONTRADO')}")
            return JsonResponse({'success': True})
        else:
            logger.warning(f"Errores en formulario de identificación: {identification_form.errors}")
            return JsonResponse({'success': False, 'errors': identification_form.errors}, status=400)
    except Exception as e:
        logger.exception(f"Error al guardar datos de identificación: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
@never_cache
def save_shipping(request):
    try:
        data = json.loads(request.body)
        shipping_form = AddressForm(data)
        if shipping_form.is_valid():
            cleaned_data = shipping_form.cleaned_data
            if 'latitude' in data and data['latitude']:
                try:
                    cleaned_data['latitude'] = float(data['latitude'])
                    logger.info(f"Latitud guardada: {cleaned_data['latitude']}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error al convertir latitud: {e}")
            if 'longitude' in data and data['longitude']:
                try:
                    cleaned_data['longitude'] = float(data['longitude'])
                    logger.info(f"Longitud guardada: {cleaned_data['longitude']}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error al convertir longitud: {e}")
            # Solo guardar si hay cambios respecto a la sesión
            if request.session.get('shipping_data') != cleaned_data:
                request.session['shipping_data'] = cleaned_data
                request.session.modified = True
                logger.info(f"Datos de envío guardados: {cleaned_data}")
            return JsonResponse({'success': True})
        else:
            logger.warning(f"Errores en formulario de envío: {shipping_form.errors}")
            return JsonResponse({'success': False, 'errors': shipping_form.errors}, status=400)
    except Exception as e:
        logger.exception(f"Error al guardar datos de envío: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@transaction.atomic
def create_order_from_session(request):
    logger.info("Iniciando create_order_from_session")
    try:
        cart = get_or_create_cart(request)
        selected_items = cart.items.filter(selected=True).select_related('product', 'variant')

        if not selected_items.exists():
            logger.error("No hay items seleccionados en el carrito al crear la orden desde sesión.")
            return None

        order_data = request.session.get('order_data_for_creation')
        if not order_data or 'identification' not in order_data or 'shipping' not in order_data:
            logger.error("Datos incompletos en sesión para crear la orden.")
            logger.info(f"Datos en sesión: {order_data}")
            return None

        identification_data = order_data['identification']
        shipping_data = order_data['shipping']

        logger.info(f"Datos de identificación: {identification_data}")
        logger.info(f"Datos de envío: {shipping_data}")

        required_fields = ['first_name', 'last_name', 'email', 'phone', 'city']
        missing_fields = []
        for field in required_fields:
            if field not in identification_data and field not in shipping_data:
                missing_fields.append(field)
            elif field in identification_data and not identification_data[field]:
                missing_fields.append(field)
            elif field in shipping_data and not shipping_data[field]:
                missing_fields.append(field)
        if missing_fields:
            logger.warning(f"Campos obligatorios faltantes: {missing_fields}")
            defaults = {
                'first_name': 'Cliente',
                'last_name': 'Tienda Virtual',
                'email': 'cliente@ejemplo.com',
                'phone': '123456789',
                'city': shipping_data.get('district', 'Lima')
            }
            for field in missing_fields:
                if field in ['first_name', 'last_name', 'email', 'phone']:
                    identification_data[field] = defaults[field]
                else:
                    shipping_data[field] = defaults[field]
            order_data = {'identification': identification_data, 'shipping': shipping_data}
            request.session['order_data_for_creation'] = order_data
            request.session.modified = True
            logger.info("Campos faltantes corregidos en la sesión")

        full_order_data = {**identification_data, **shipping_data}
        # Asegurarse de que latitude y longitude estén presentes en full_order_data
        if 'latitude' not in full_order_data or full_order_data['latitude'] in [None, '']:
            full_order_data['latitude'] = shipping_data.get('latitude') or identification_data.get('latitude')
        if 'longitude' not in full_order_data or full_order_data['longitude'] in [None, '']:
            full_order_data['longitude'] = shipping_data.get('longitude') or identification_data.get('longitude')
        
        if request.user.is_authenticated:
            full_order_data['user'] = request.user
            logger.info(f"Usuario autenticado: {request.user.username}")
        else:
            logger.info("Usuario no autenticado, creando orden sin usuario asociado")
        
        payment_id = request.GET.get('payment_id', '')
        status = request.GET.get('status', 'pending')
        preference_id = request.session.get('preference_id', '')
        
        if payment_id and not isinstance(payment_id, str):
            logger.warning(f"payment_id no es una cadena válida: {payment_id}, convirtiendo a string")
            payment_id = str(payment_id)
            
        payment_data = {
            'payment_id': payment_id,
            'status': status,
            'preference_id': preference_id,
            'external_reference': order_data.get('email', ''),
            'request_token': str(time.time())  # Usar timestamp como token único
        }
        
        logger.info(f"Datos de pago completos: {payment_data}")
        
        logger.info(f"Datos de pago preparados: payment_id={payment_id}, status={status}, preference_id={preference_id}")
        
        existing_order = None
        if payment_id:
            existing_order = Order.objects.filter(payment_id=payment_id).first()
            if existing_order:
                logger.info(f"Se encontró una orden existente con payment_id={payment_id}")
                return existing_order
                
        if not existing_order and preference_id:
            existing_order = Order.objects.filter(payment_preference_id=preference_id).first()
            if existing_order:
                logger.info(f"Se encontró una orden existente con preference_id={preference_id}")
                return existing_order
        
        from .utils import create_order_from_cart
        
        logger.info("Iniciando transacción atómica para crear orden")
        order = create_order_from_cart(cart, full_order_data, payment_data)
        
        if not order:
            logger.error("No se pudo crear la orden utilizando la función de utilidad.")
            return None
            
        verification_order = Order.objects.filter(id=order.id).first()
        if not verification_order:
            logger.error(f"La orden con ID {order.id} no se encontró en la base de datos después de crearla")
            return None
        
        logger.info(f"Orden {order.id} creada correctamente desde la sesión.")
        
        if request.user.is_authenticated and full_order_data.get('save_address'):
            from .utils import save_address_to_user
            existing_address = Address.objects.filter(
                user=request.user,
                department=full_order_data['department'],
                province=full_order_data['province'],
                district=full_order_data['district'],
                street=full_order_data['street'],
                street_number=full_order_data['street_number'],
                additional_info=full_order_data.get('additional_info', '')
            ).first()
            if not existing_address:
                address = save_address_to_user(request.user, full_order_data)
                if address:
                    logger.info(f"Dirección guardada para el usuario {request.user.username}")
            else:
                logger.info(f"Dirección ya existe para el usuario {request.user.username}, no se guardó duplicado")
        
        for key in ['checkout_step', 'identification_data', 'shipping_data', 'order_data_for_creation']:
            request.session.pop(key, None)
        request.session.modified = True
        logger.info("Datos de checkout limpiados de la sesión")

        return order

    except Exception as e:
        logger.exception(f"Error inesperado en create_order_from_session: {e}")
        return None

@never_cache
def payment_success(request):
    logger.info(f"Acceso a payment_success. Query Params: {request.GET}")
    try:
        payment_id = request.GET.get('payment_id')
        status = request.GET.get('status')
        preference_id = request.GET.get('preference_id')
        session_preference_id = request.session.get('preference_id')
        order_id = request.session.get('order_id')

        logger.info(f"Datos de pago recibidos: payment_id={payment_id}, status={status}, preference_id={preference_id}, order_id={order_id}")

        if not payment_id or not status or not order_id:
            logger.warning("Faltan parámetros payment_id, status o order_id en payment_success")
            messages.error(request, "Información de pago incompleta.")
            return redirect('orders:payment_failure')

        order = Order.objects.get(id=order_id)
        
        if preference_id and session_preference_id and preference_id != session_preference_id:
            logger.error(f"Discrepancia de Preference ID: Sesión={session_preference_id}, MP={preference_id}")
            messages.error(request, "Error de validación del pago.")
            return redirect('orders:payment_failure')

        order.payment_id = str(payment_id)
        order.payment_status = status
        order.paid = (status == 'approved')
        order.status = 'completed' if status == 'approved' else 'pending'
        if preference_id and not order.payment_preference_id:
            order.payment_preference_id = preference_id
        # Guardar external_reference y request_token si están disponibles
        external_reference = request.GET.get('external_reference')
        if external_reference and not order.external_reference:
            order.external_reference = external_reference
            logger.info(f"External reference guardado: {external_reference}")
        request_token = request.GET.get('request_token')
        if request_token and not order.request_token:
            order.request_token = request_token
            logger.info(f"Request token guardado: {request_token}")
        order.save()
        logger.info(f"Orden actualizada con datos de pago: payment_id={order.payment_id}, status={order.payment_status}, preference_id={order.payment_preference_id}, external_reference={order.external_reference}, request_token={order.request_token}")
        
        logger.info(f"Orden {order.id} actualizada: payment_id={payment_id}, status={status}, paid={order.paid}")

        if order.paid:
            from .utils import reduce_stock_from_order
            success, error_msg = reduce_stock_from_order(order)
            if not success:
                logger.error(f"No se pudo reducir stock para orden {order.id}: {error_msg}")
                messages.warning(request, f"Pago aprobado, pero hubo un problema con el inventario: {error_msg}. Contacte a soporte.")
            
            cart = get_or_create_cart(request)
            cart.items.filter(selected=True).delete()
            if cart.coupon:
                cart.coupon = None
                cart.discount = 0
                cart.save()
            logger.info(f"Carrito {cart.id} limpiado después de pago exitoso.")

            for key in ['preference_id', 'init_point', 'order_data_for_creation', 'order_id', 'identification_data', 'shipping_data']:
                request.session.pop(key, None)
            request.session.modified = True

            messages.success(request, "¡Tu pago ha sido aprobado y tu pedido está confirmado!")
            return render(request, 'orders/order_confirmation.html', {'order': order})
        else:
            logger.warning(f"Pago recibido pero no aprobado. Estado: {status}. Orden: {order.id}")
            if status == 'pending' or status == 'in_process':
                return redirect('orders:payment_pending')
            else:
                return redirect('orders:payment_failure')
                
    except Order.DoesNotExist:
        logger.error(f"Orden con ID {order_id} no encontrada en payment_success")
        messages.error(request, "No se pudo encontrar la orden.")
        return redirect('orders:payment_failure')
    except Exception as e:
        logger.exception(f"Error inesperado en payment_success: {e}")
        messages.error(request, "Ocurrió un error al procesar tu pago. Por favor, contacta a soporte.")
        return redirect('orders:payment_failure')

@never_cache
def payment_pending(request):
    logger.info(f"Acceso a payment_pending. Query Params: {request.GET}")
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status', 'pending')
    preference_id = request.GET.get('preference_id')
    session_preference_id = request.session.get('preference_id')
    order_id = request.session.get('order_id')
    
    logger.info(f"Datos de pago recibidos: payment_id={payment_id}, status={status}, preference_id={preference_id}, order_id={order_id}")
    
    try:
        if not order_id:
            logger.error("No se encontró order_id en la sesión")
            messages.error(request, "No se pudo encontrar la orden.")
            return render(request, 'orders/payment_status.html', {'status': 'pending', 'order': None})
        
        order = Order.objects.get(id=order_id)
        order.payment_status = status
        order.paid = False
        if payment_id and not order.payment_id:
            order.payment_id = payment_id
        if preference_id and not order.payment_preference_id:
            order.payment_preference_id = preference_id
        order.save()
        logger.info(f"Orden {order.id} actualizada como pendiente.")
        
        messages.info(request, "Tu pago está pendiente de confirmación. Te notificaremos cuando se complete.")
        return render(request, 'orders/payment_status.html', {'status': 'pending', 'order': order})
        
    except Order.DoesNotExist:
        logger.error(f"Orden con ID {order_id} no encontrada en payment_pending")
        messages.error(request, "No se pudo encontrar la orden.")
        return render(request, 'orders/payment_status.html', {'status': 'pending', 'order': None})
    except Exception as e:
        logger.exception(f"Error inesperado en payment_pending: {e}")
        messages.error(request, "Ocurrió un error al procesar tu pago. Por favor, contacta a soporte.")
        return render(request, 'orders/payment_status.html', {'status': 'pending', 'order': None})

@never_cache
def payment_failure(request):
    logger.warning(f"Acceso a payment_failure. Query Params: {request.GET}")
    session_preference_id = request.session.get('preference_id')
    order_id = request.session.get('order_id')
    order = None
    
    try:
        if order_id:
            order = Order.objects.get(id=order_id)
            order.payment_status = request.GET.get('status', 'failure')
            order.paid = False
            order.save()
            logger.info(f"Orden {order.id} marcada como fallida.")
        
        for key in ['preference_id', 'init_point', 'order_data_for_creation', 'order_id', 'identification_data', 'shipping_data']:
            request.session.pop(key, None)
        request.session.modified = True
        
        messages.error(request, "Tu pago no pudo ser procesado. Por favor, inténtalo de nuevo o contacta a soporte.")
        return render(request, 'orders/payment_status.html', {'status': 'failure', 'order': order})
        
    except Order.DoesNotExist:
        logger.error(f"Orden con ID {order_id} no encontrada en payment_failure")
        messages.error(request, "No se pudo encontrar la orden.")
        return render(request, 'orders/payment_status.html', {'status': 'failure', 'order': None})
    except Exception as e:
        logger.exception(f"Error inesperado en payment_failure: {e}")
        messages.error(request, "Ocurrió un error al procesar tu pago. Por favor, contacta a soporte.")
        return render(request, 'orders/payment_status.html', {'status': 'failure', 'order': None})

@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    logger.info("Webhook de Mercado Pago recibido")
    try:
        data = json.loads(request.body)
        logger.info(f"Datos del webhook: {data}")
        
        if 'data' in data and 'id' in data.get('data', {}):
            payment_id = data['data']['id']
            logger.info(f"Notificación de pago recibida para payment_id: {payment_id}")
            
            order = Order.objects.filter(payment_id=payment_id).first()
            if not order and 'external_reference' in data:
                external_reference = data.get('external_reference', '')
                if external_reference.startswith('cart_'):
                    try:
                        order_id = external_reference.split('_order_')[-1]
                        order = Order.objects.filter(id=order_id).first()
                    except IndexError:
                        logger.warning(f"Formato de external_reference inválido: {external_reference}")
            
            if order:
                sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
                try:
                    payment_info = sdk.payment().get(payment_id)
                    if payment_info['status'] == 200:
                        payment_data = payment_info['response']
                        status = payment_data.get('status', '')
                        logger.info(f"Estado del pago: {status}")
                        
                        order.payment_status = status
                        order.paid = (status == 'approved')
                        if order.paid:
                            order.status = 'completed'
                            from .utils import reduce_stock_from_order
                            success, error_msg = reduce_stock_from_order(order)
                            if not success:
                                logger.error(f"Webhook: no se pudo reducir stock para orden {order.id}: {error_msg}")
                        elif status in ['rejected', 'cancelled']:
                            order.status = 'cancelled'
                        else:
                            order.status = 'pending'
                        
                        order.save()
                        logger.info(f"Orden {order.id} actualizada desde webhook con estado: {status}")
                    else:
                        logger.error(f"Error al obtener información del pago: {payment_info}")
                except Exception as e:
                    logger.exception(f"Error al consultar pago en webhook: {e}")
            else:
                logger.warning(f"No se encontró orden con payment_id: {payment_id}")
        else:
            logger.info("Webhook recibido pero no es una notificación de pago o no contiene ID")
            
        return JsonResponse({'status': 'ok'})
    except json.JSONDecodeError:
        logger.error("Error al decodificar JSON del webhook")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.exception(f"Error procesando webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_confirmation.html', {'order': order})