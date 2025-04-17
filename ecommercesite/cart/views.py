from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.http import JsonResponse, HttpResponse
from products.models import Product, ProductVariant
from .models import Cart, CartItem
import mercadopago
from django.conf import settings
from decimal import Decimal
from django.contrib.auth.decorators import login_required
import json
import logging
from django.contrib import messages

logger = logging.getLogger(__name__)

def get_or_create_cart(request):
    try:
        if request.user.is_authenticated:
            # Usuario autenticado: obtener o crear carrito asociado al usuario
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            # Si se acaba de crear un carrito para el usuario y hay un carrito en sesión,
            # transferir los items del carrito de sesión al carrito del usuario
            if created and 'cart_id' in request.session:
                old_cart = Cart.objects.filter(id=request.session['cart_id']).first()
                if old_cart and old_cart.items.exists():
                    for item in old_cart.items.all():
                        # Usar update_or_create para manejar duplicados
                        cart_item, _ = CartItem.objects.get_or_create(
                            cart=cart, 
                            product=item.product, 
                            variant=item.variant,
                            defaults={'quantity': item.quantity, 'selected': item.selected}
                        )
                        # Si el item ya existía, sumar las cantidades
                        if not _:
                            cart_item.quantity += item.quantity
                            cart_item.save()
                    # Eliminar el carrito antiguo después de transferir los items
                    old_cart.delete()
                # Eliminar el ID del carrito de la sesión
                del request.session['cart_id']
        else:
            # Usuario anónimo: obtener o crear carrito basado en la sesión
            cart_id = request.session.get('cart_id')
            if cart_id:
                cart = Cart.objects.filter(id=cart_id).first()
                if not cart:
                    # Si el carrito no existe (fue eliminado), crear uno nuevo
                    cart = Cart.objects.create()
                    request.session['cart_id'] = cart.id
            else:
                # Si no hay ID de carrito en la sesión, crear uno nuevo
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
                
        # Asegurar que la sesión se guarde
        if not request.user.is_authenticated:
            request.session.modified = True
            
        return cart
    except Exception as e:
        # Registrar el error y crear un carrito nuevo como fallback
        logger.error(f"Error al obtener/crear carrito: {e}")
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id
        request.session.modified = True
        return cart

@require_POST
def create_payment(request):
    try:
        # Verificar que el token de MercadoPago esté configurado
        if not hasattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN') or not settings.MERCADO_PAGO_ACCESS_TOKEN:
            logger.error("Token de MercadoPago no configurado")
            return JsonResponse({"error": "Error de configuración del sistema de pagos"}, status=500)
            
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        cart = get_or_create_cart(request)
        
        # Verificar que el carrito tenga items
        if not cart.items.exists():
            return JsonResponse({"error": "El carrito está vacío"}, status=400)

        # Verificar que haya items seleccionados
        selected_items = cart.items.filter(selected=True)
        if not selected_items.exists():
            return JsonResponse({"error": "No hay productos seleccionados para pagar"}, status=400)

        # Verificar stock de los productos seleccionados
        for item in selected_items:
            stock = float('inf')  # Valor por defecto si no hay control de stock
            if item.variant and hasattr(item.variant, 'stock') and item.variant.stock is not None:
                stock = item.variant.stock
            elif hasattr(item.product, 'stock') and item.product.stock is not None:
                stock = item.product.stock
                
            if item.quantity > stock:
                return JsonResponse({
                    "error": f"No hay suficiente stock de {item.product.name}. Solo quedan {stock} unidades."
                }, status=400)

        # Crear items para la preferencia de pago
        items = []
        for item in selected_items:
            unit_price = item.total_price() / item.quantity
            product_name = item.product.name
            if item.variant:
                variant_info = f"{item.variant.color or ''} {item.variant.size or ''}".strip()
                if variant_info:
                    product_name = f"{product_name} ({variant_info})"
                    
            items.append({
                "title": product_name[:100],  # Limitar longitud para evitar errores
                "quantity": item.quantity,
                "unit_price": float(unit_price),
                "currency_id": "PEN",  # Moneda peruana (soles)
            })
        
        # Agregar costo de envío si aplica
        if cart.shipping_cost > 0:
            items.append({
                "title": "Costo de envío",
                "quantity": 1,
                "unit_price": float(cart.shipping_cost),
                "currency_id": "PEN",
            })

        # Configurar URLs de retorno dinámicas basadas en la URL actual
        base_url = request.build_absolute_uri('/').rstrip('/')
        preference_data = {
            "items": items,
            "back_urls": {
                "success": f"{base_url}/cart/success/",
                "failure": f"{base_url}/cart/failure/",
                "pending": f"{base_url}/cart/pending/",
            },
            "auto_return": "approved",
            "statement_descriptor": "Tienda Virtual",  # Descripción que aparecerá en el estado de cuenta
            "external_reference": str(cart.id),  # Referencia para identificar el carrito
        }

        # Crear preferencia en MercadoPago
        try:
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response["response"]
            
            # Registrar información para debugging
            logger.info(f"Preferencia de pago creada: ID {preference['id']}")
            
            return JsonResponse({
                "init_point": preference["init_point"],
                "preference_id": preference["id"]
            })
        except Exception as e:
            logger.error(f"Error al crear preferencia en MercadoPago: {str(e)}")
            return JsonResponse({"error": "Error al conectar con el servicio de pagos. Intente nuevamente."}, status=500)
            
    except Exception as e:
        logger.error(f"Error inesperado al crear pago: {str(e)}")
        return JsonResponse({"error": "Error inesperado al procesar el pago. Intente nuevamente."}, status=500)

@require_POST
def cart_add(request, product_id):
    cart = get_or_create_cart(request)
    try:
        # Intentar obtener datos del cuerpo JSON o formulario
        data = {}
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        elif request.POST:
            data = request.POST.dict()
        # Si hay datos HTMX en hx-vals o no se encontraron datos, intentar con request.body
        if not data and request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                # Si no podemos decodificar JSON, usar valores predeterminados
                data = {}
        
        logger.info(f"Datos recibidos para agregar al carrito: {data}")
        
        # Obtener y validar variant_id
        variant_id = data.get('variant_id')
        if variant_id and not isinstance(variant_id, (int, str)) or (isinstance(variant_id, str) and not variant_id.isdigit()):
            logger.error(f"ID de variante inválido: {variant_id}")
            return JsonResponse({'success': False, 'message': 'ID de variante inválido'}, status=400)
        
        # Obtener y validar quantity
        try:
            quantity = int(data.get('quantity', 1))
            if quantity <= 0:
                logger.error("La cantidad debe ser mayor a 0.")
                return JsonResponse({'success': False, 'message': 'La cantidad debe ser mayor a 0.'}, status=400)
        except (ValueError, TypeError):
            logger.error(f"Cantidad inválida: {data.get('quantity')}")
            return JsonResponse({'success': False, 'message': 'Cantidad inválida'}, status=400)

        # Obtener producto
        try:
            product = get_object_or_404(Product, id=product_id, available=True)
            logger.info(f"Producto encontrado: {product}")
        except Exception as e:
            logger.error(f"Error al obtener producto {product_id}: {e}")
            return JsonResponse({'success': False, 'message': 'Producto no encontrado o no disponible'}, status=404)

        # Obtener variante si existe
        variant = None
        if variant_id:
            try:
                variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
                logger.info(f"Variante encontrada: {variant}")
            except Exception as e:
                logger.error(f"Error al obtener variante {variant_id}: {e}")
                return JsonResponse({'success': False, 'message': 'Variante no encontrada'}, status=404)

        # Verificar stock antes de agregar al carrito
        stock = float('inf')  # Valor por defecto si no hay control de stock
        if variant and hasattr(variant, 'stock') and variant.stock is not None:
            stock = variant.stock
        elif hasattr(product, 'stock') and product.stock is not None:
            stock = product.stock
            
        if quantity > stock:
            logger.warning(f"Cantidad solicitada ({quantity}) excede el stock disponible ({stock})")
            return JsonResponse({
                'success': False, 
                'message': f'Solo hay {stock} unidades disponibles de este producto'
            }, status=400)

        # Crear o actualizar item en el carrito
        if variant:
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant)
        else:
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=None)

        # Actualizar cantidad
        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > stock:
                logger.warning(f"Cantidad total ({new_quantity}) excedería el stock disponible ({stock})")
                return JsonResponse({
                    'success': False, 
                    'message': f'No se puede agregar {quantity} más. Solo hay {stock} unidades disponibles en total.'
                }, status=400)
            cart_item.quantity = new_quantity
        else:
            cart_item.quantity = quantity
            
        cart_item.selected = True  # Asegurar que los nuevos items estén seleccionados por defecto
        cart_item.save()

        logger.info(f"Producto agregado al carrito: {cart_item}")
        
        # Verificar si la solicitud es AJAX/HTMX o una solicitud normal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('HX-Request'):
            # Para solicitudes HTMX, renderizar el contenido actualizado del carrito
            total = cart.get_final_total()
            response = render(request, 'cart/cart_partial.html', {
                'cart': cart,
                'total': total,
                'csrf_token': request.POST.get('csrfmiddlewaretoken'),
            })
            response['X-Cart-Total'] = str(total)
            response['X-Trigger-Cart-Update'] = 'true'
            return response
        else:
            # Para solicitudes normales, redirigir al carrito
            return redirect('cart:cart_detail')
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}")
        return JsonResponse({'success': False, 'message': 'Error en los datos enviados.'}, status=400)
    except Exception as e:
        logger.error(f"Error inesperado al agregar al carrito: {e}")
        return JsonResponse({'success': False, 'message': 'Error al agregar el producto al carrito. Intente nuevamente.'}, status=500)

@login_required
def cart_detail(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.info(request, "Tu carrito está vacío.")
    for item in cart.items.all():
        item.user_has_purchased = item.product.user_has_purchased(request.user)
    suggestions = Product.objects.exclude(id__in=[item.product.id for item in cart.items.all()]).select_related('brand').order_by('?')[:3]
    return render(request, 'cart/detail.html', {
        'cart': cart,
        'total': cart.get_final_total(),
        'suggestions': suggestions
    })


@require_GET
def get_suggestions(request):
    cart = get_or_create_cart(request)
    suggestions = Product.objects.exclude(id__in=[item.product.id for item in cart.items.all()]).order_by('?')[:3]
    return render(request, 'cart/suggestions_partial.html', {'suggestions': suggestions})

@require_GET
def get_summary(request):
    """Devuelve un resumen del carrito en formato JSON para actualizaciones AJAX"""
    cart = get_or_create_cart(request)
    total_items = sum(item.quantity for item in cart.items.all())
    total_price = cart.get_final_total()
    
    return JsonResponse({
        'total_items': total_items,
        'total_price': float(total_price),
        'shipping_cost': float(cart.shipping_cost) if cart.shipping_cost else 0,
        'subtotal': float(cart.get_subtotal())
    })

@require_http_methods(["DELETE"])
def remove_item(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    
    total = cart.get_final_total()
    if request.headers.get('HX-Request'):
        response = render(request, 'cart/cart_partial.html', {
            'cart': cart,
            'total': total,
            'csrf_token': request.POST.get('csrfmiddlewaretoken'),
        })
        response['X-Cart-Total'] = str(total)
        response['X-Trigger-Cart-Update'] = 'true'
        return response
    
    return HttpResponse(status=204)

@require_POST
def increase_quantity(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    # Verificar si el producto o variante tiene stock definido
    if item.variant:
        if hasattr(item.variant, 'stock') and item.variant.stock is not None:
            stock = item.variant.stock
        else:
            # Si no tiene stock definido, permitir aumentar
            stock = float('inf')
    else:
        if hasattr(item.product, 'stock') and item.product.stock is not None:
            stock = item.product.stock
        else:
            # Si no tiene stock definido, permitir aumentar
            stock = float('inf')
    
    if item.quantity < stock:
        item.quantity += 1
        item.save()
    else:
        messages.warning(request, f"No se puede aumentar la cantidad. Solo hay {stock} unidades disponibles.")
    
    total = cart.get_final_total()
    if request.headers.get('HX-Request'):
        csrf_token = request.COOKIES.get('csrftoken') or request.POST.get('csrfmiddlewaretoken')
        response = render(request, 'cart/cart_partial.html', {
            'cart': cart,
            'total': total,
            'csrf_token': csrf_token,
        })
        response['X-Cart-Total'] = str(total)
        response['X-Trigger-Cart-Update'] = 'true'
        return response
    return HttpResponse(status=204)

@require_POST
def decrease_quantity(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        # Si la cantidad es 1 y se intenta disminuir, mostrar mensaje
        messages.info(request, "La cantidad mínima es 1. Si desea eliminar el producto, use el botón de eliminar.")
    
    total = cart.get_final_total()
    if request.headers.get('HX-Request'):
        csrf_token = request.COOKIES.get('csrftoken') or request.POST.get('csrfmiddlewaretoken')
        response = render(request, 'cart/cart_partial.html', {
            'cart': cart,
            'total': total,
            'csrf_token': csrf_token,
        })
        response['X-Cart-Total'] = str(total)
        response['X-Trigger-Cart-Update'] = 'true'
        return response
    return HttpResponse(status=204)

@require_POST
def update_quantity(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    try:
        new_quantity = int(request.POST.get('quantity', item.quantity))
        if new_quantity <= 0:
            messages.warning(request, "La cantidad debe ser mayor a 0.")
            new_quantity = 1
    except (ValueError, TypeError):
        messages.warning(request, "Cantidad inválida. Se mantendrá la cantidad actual.")
        new_quantity = item.quantity
    
    # Determinar el stock disponible
    stock = float('inf')  # Valor por defecto si no hay control de stock
    if item.variant and hasattr(item.variant, 'stock') and item.variant.stock is not None:
        stock = item.variant.stock
    elif hasattr(item.product, 'stock') and item.product.stock is not None:
        stock = item.product.stock
    
    # Ajustar la cantidad según el stock disponible
    if new_quantity > stock:
        messages.warning(request, f"Solo hay {stock} unidades disponibles de este producto.")
        new_quantity = stock
    
    # Actualizar la cantidad
    item.quantity = max(1, new_quantity)
    item.save()
    
    # Calcular el nuevo total del carrito
    total = cart.get_final_total()
    
    # Responder según el tipo de solicitud
    if request.headers.get('HX-Request'):
        csrf_token = request.COOKIES.get('csrftoken') or request.POST.get('csrfmiddlewaretoken')
        response = render(request, 'cart/cart_item.html', {
            'item': item, 
            'csrf_token': csrf_token
        })
        response['X-Cart-Total'] = str(total)
        response['X-Trigger-Cart-Update'] = 'true'
        return response
    
    return HttpResponse(status=204)

@require_GET
def get_summary(request):
    cart = get_or_create_cart(request)
    total = cart.get_final_total()
    context = {
        'cart': cart,
        'total': total,
        'shipping_cost': cart.shipping_cost,
        'shipping_discount': cart.shipping_discount
    }
    response = render(request, 'cart/cart_summary_partial.html', context)
    response['X-Cart-Total'] = str(total)
    return response

@require_POST
def toggle_select(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.selected = not item.selected
    item.save()
    
    total = cart.get_final_total()
    if request.headers.get('HX-Request'):
        response = render(request, 'cart/cart_partial.html', {'cart': cart, 'total': total})
        response['X-Cart-Total'] = str(total)
        response['X-Trigger-Cart-Update'] = 'true'
        return response
    return redirect('cart:cart_detail')

@require_POST
def toggle_select_all(request):
    cart = get_or_create_cart(request)
    all_selected = cart.all_items_selected()
    cart.items.update(selected=not all_selected)
    total = cart.get_final_total()
    response = render(request, 'cart/cart_partial.html', {'cart': cart, 'total': total})
    response['X-Cart-Total'] = str(total)
    response['X-Trigger-Cart-Update'] = 'true'
    return response

def payment_success(request):
    return render(request, 'cart/payment_success.html')

def payment_failure(request):
    return render(request, 'cart/payment_failure.html')

def payment_pending(request):
    return render(request, 'cart/payment_pending.html')
