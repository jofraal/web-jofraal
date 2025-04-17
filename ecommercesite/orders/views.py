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

logger = logging.getLogger(__name__)

# Vistas API para manejar las solicitudes AJAX de ubicaciones
def get_departments_api(request):
    """Vista API para obtener la lista de departamentos"""
    departments = get_departments()
    # Asegurarse de que departments sea una lista, incluso si está vacía
    if not isinstance(departments, list):
        departments = list(departments) if departments else []
    return JsonResponse(departments, safe=False)

def get_provinces_api(request):
    """Vista API para obtener las provincias de un departamento"""
    department = request.GET.get('department', '')
    if not department:
        return JsonResponse({'error': 'Departamento no especificado'}, status=400)
    
    provinces = get_provinces(department)
    # Asegurarse de que provinces sea una lista, incluso si está vacía
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
    # Asegurarse de que districts sea una lista, incluso si está vacía
    if not isinstance(districts, list):
        districts = list(districts) if districts else []
    return JsonResponse(districts, safe=False)


def delivery_form(request):
    # Esta función ha sido reemplazada por checkout
    # Redirigir a la nueva vista de checkout
    return redirect('orders:checkout')


@require_POST
@never_cache
def create_payment(request):
    try:
        # Verificar credenciales
        if not hasattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN') or not settings.MERCADO_PAGO_ACCESS_TOKEN:
            logger.error("Token de MercadoPago no configurado")
            return JsonResponse({"error": "Error de configuración del sistema de pagos"}, status=500)

        # Obtener datos del formulario
        data = request.POST
        email = data.get('cardholderEmail')
        transaction_amount = data.get('transaction_amount')

        if not email:
            logger.error("Correo electrónico no proporcionado")
            return JsonResponse({"error": "Correo electrónico requerido"}, status=400)
        
        try:
            transaction_amount = float(transaction_amount)
        except (TypeError, ValueError):
            logger.error("Monto de transacción inválido")
            return JsonResponse({"error": "Monto de transacción inválido"}, status=400)

        # Validar datos de envío
        shipping_form = OrderShippingForm(data)
        if not shipping_form.is_valid():
            logger.error(f"Errores en formulario de envío: {shipping_form.errors}")
            return JsonResponse({"error": "Datos de envío inválidos", "details": shipping_form.errors}, status=400)

        # Obtener carrito con prefetch para optimizar consultas
        cart = get_or_create_cart(request)
        selected_items = cart.items.filter(selected=True).select_related('product', 'variant')
        if not selected_items.exists():
            logger.error("No hay productos seleccionados en el carrito")
            return JsonResponse({"error": "No hay productos seleccionados"}, status=400)

        # Inicializar Mercado Pago
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

        # Crear items para la preferencia
        items = []
        for item in selected_items:
            product_name = item.product.name
            if hasattr(item, 'variant') and item.variant:
                variant_info = []
                if item.variant.color:
                    variant_info.append(f"Color: {item.variant.color}")
                if item.variant.size:
                    variant_info.append(f"Talla: {item.variant.size}")
                if variant_info:
                    product_name = f"{product_name} ({', '.join(variant_info)})"
            
            items.append({
                "title": product_name[:100],
                "quantity": item.quantity,
                "unit_price": float(item.total_price() / item.quantity),
                "currency_id": "PEN"
            })

        # Crear preferencia
        preference_data = {
            "items": items,
            "payer": {
                "email": email
            },
            "back_urls": {
                "success": request.build_absolute_uri('/orders/success/'),
                "failure": request.build_absolute_uri('/orders/failure/'),
                "pending": request.build_absolute_uri('/orders/pending/')
            },
            "auto_return": "approved",
            "statement_descriptor": "Tienda Virtual",
            "external_reference": f"cart_{cart.id}"
        }

        # Crear preferencia en Mercado Pago
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        logger.info(f"Preferencia creada: ID {preference['id']}")

        # Usar transacción para garantizar la integridad de los datos
        with transaction.atomic():
            # Crear orden
            identification_data = request.session.get('identification_data', {})
            order = shipping_form.save(commit=False)
            order.email = email
            order.status = 'pending'
            order.first_name = identification_data.get('first_name', '')
            order.last_name = identification_data.get('last_name', '')
            order.phone = identification_data.get('phone', '')
            order.invoice_requested = identification_data.get('invoice_requested', False)
            
            # Asegurarse de que el campo city tenga un valor
            if not order.city:
                order.city = order.district  # Usar el distrito como valor predeterminado si no se proporciona ciudad
            
            # Verificar si el usuario está autenticado
            if request.user.is_authenticated:
                order.user = request.user
                logger.info(f"Usuario autenticado con ID {request.user.id} asignado a la orden")
            else:
                order.user = None
                logger.info("Usuario no autenticado, la orden se creará sin usuario asociado.")
            
            # Guardar la orden
            order.save()
            logger.info(f"Orden creada exitosamente con ID: {order.id}")

            # Crear items de la orden de manera optimizada
            order_items = []
            for item in selected_items:
                unit_price = item.total_price() / item.quantity if item.quantity > 0 else Decimal('0.00')
                variant_info = ""
                if hasattr(item, 'variant') and item.variant:
                    variant_parts = []
                    if item.variant.color:
                        variant_parts.append(f"Color: {item.variant.color}")
                    if item.variant.size:
                        variant_parts.append(f"Talla: {item.variant.size}")
                    variant_info = ", ".join(variant_parts)
                
                order_items.append(OrderItem(
                    order=order,
                    product=item.product,
                    price=unit_price,
                    quantity=item.quantity,
                    variant_info=variant_info
                ))
            
            # Crear todos los items en una sola operación de base de datos
            OrderItem.objects.bulk_create(order_items)

        # Guardar order_id en sesión
        request.session['order_id'] = order.id

        # Devolver ID de preferencia para HTMX
        return JsonResponse({
            "id": preference["id"]
        })

    except mercadopago.sdk.MPException as mp_error:
        logger.error(f"Error de Mercado Pago: {str(mp_error)}")
        return JsonResponse({"error": f"Error de Mercado Pago: {str(mp_error)}"}, status=500)
    except Exception as e:
        logger.error(f"Error inesperado al crear pago: {str(e)}")
        return JsonResponse({"error": f"Error al procesar el pago: {str(e)}"}, status=500)

@never_cache
def payment_success(request):
    order_id = request.session.get('order_id')
    if not order_id:
        messages.warning(request, "No se encontró la orden relacionada con el pago.")
        return redirect('cart:cart_detail')
        
    order = get_object_or_404(Order, id=order_id)
    
    # Usar transacción para garantizar la integridad de los datos
    with transaction.atomic():
        # Actualizar estado de la orden
        order.status = 'paid'
        order.paid = True
        order.save()
        
        # Limpiar carrito
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id)
                if cart.all_items_selected():
                    cart.delete()
                    if 'cart_id' in request.session:
                        del request.session['cart_id']
                else:
                    cart.items.filter(selected=True).delete()
            except Cart.DoesNotExist:
                pass
    
    # Limpiar sesión
    if 'order_id' in request.session:
        del request.session['order_id']
    
    # Mostrar mensaje de éxito
    messages.success(request, "¡Tu pago ha sido procesado correctamente! Gracias por tu compra.")
    
    return redirect("orders:order_confirmation", order.id)

def payment_failure(request):
    messages.error(request, "El pago no pudo ser procesado. Por favor, intente nuevamente.")
    return redirect('orders:checkout')

def payment_pending(request):
    messages.info(request, "El pago está pendiente de confirmación. Le notificaremos cuando se complete.")
    return redirect('cart:cart_detail')

def order_create(request):
    return redirect('orders:checkout')

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "orders/order_confirmation.html", {"order": order})

@never_cache
def checkout(request):
    # Obtener carrito con prefetch para optimizar consultas
    cart = get_or_create_cart(request)
    if not cart:
        messages.warning(request, "No tienes productos en el carrito.")
        return redirect('cart:cart_detail')

    # Optimizar consultas con select_related
    selected_items = cart.items.filter(selected=True).select_related('product', 'variant')
    
    # Verificar si hay productos seleccionados
    if not selected_items.exists():
        messages.warning(request, "No has seleccionado ningún producto para comprar.")
        return redirect('cart:cart_detail')

    # Asegurarse de que el descuento de envío se calcule correctamente
    total = cart.get_final_total()

    identification_form = OrderIdentificationForm(request.POST or None)
    shipping_form = OrderShippingForm(request.POST or None)

    active_step = 'identification'
    if request.method == 'POST':
        step = request.POST.get('step')
        if step == 'identification':
            if identification_form.is_valid():
                # Guardar datos de identificación en sesión
                request.session['identification_data'] = identification_form.cleaned_data
                active_step = 'shipping'
            else:
                # Mostrar errores de validación
                for field, errors in identification_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        elif step == 'shipping':
            # No creamos la orden aquí porque el botón usa HTMX
            if shipping_form.is_valid():
                # Los datos se envían a create_payment vía HTMX
                pass
            else:
                # Mostrar errores de validación
                for field, errors in shipping_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': shipping_form.errors})
    else:
        # Prellenar formulario con datos del usuario autenticado
        if request.user.is_authenticated:
            identification_form = OrderIdentificationForm(initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'phone': getattr(request.user, 'phone', ''),  # Si el usuario tiene un campo phone
            })
        
        # Recuperar datos de identificación de sesión si existen
        identification_data = request.session.get('identification_data', {})
        if identification_data:
            identification_form = OrderIdentificationForm(initial=identification_data)
            active_step = "shipping"

    return render(request, "orders/checkout.html", {
        "cart": cart,
        "selected_items": selected_items,
        "total": total,
        "identification_form": identification_form,
        "shipping_form": shipping_form,
        "active_step": active_step,
        "MERCADOPAGO_PUBLIC_KEY": settings.MERCADO_PAGO_PUBLIC_KEY,
        "identification_data": request.session.get('identification_data', {})
    })