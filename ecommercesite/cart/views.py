from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.views.decorators.cache import never_cache
from django.http import JsonResponse, HttpResponse
from products.models import Product, ProductVariant
from orders.models import OrderItem
from .models import Cart, CartItem
from django.db.models import Sum
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
            cart, created = Cart.objects.get_or_create(user=request.user)
            if created and 'cart_id' in request.session:
                old_cart = Cart.objects.filter(id=request.session['cart_id']).first()
                if old_cart and old_cart.items.exists():
                    for item in old_cart.items.all():
                        cart_item, _ = CartItem.objects.get_or_create(
                            cart=cart, 
                            product=item.product, 
                            variant=item.variant,
                            defaults={'quantity': item.quantity, 'selected': item.selected}
                        )
                        if not _:
                            cart_item.quantity += item.quantity
                            cart_item.save()
                    old_cart.delete()
                del request.session['cart_id']
        else:
            cart_id = request.session.get('cart_id')
            if cart_id:
                cart = Cart.objects.filter(id=cart_id).first()
                if not cart:
                    cart = Cart.objects.create()
                    request.session['cart_id'] = cart.id
            else:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
                
        if not request.user.is_authenticated:
            request.session.modified = True
            
        return cart
    except Exception as e:
        logger.error(f"Error al obtener/crear carrito: {e}")
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id
        request.session.modified = True
        return cart

@require_POST
def cart_add(request, product_id):
    cart = get_or_create_cart(request)
    try:
        data = {}
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        elif request.POST:
            data = request.POST.dict()
        if not data and request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                data = {}
        
        logger.info(f"Datos recibidos para agregar al carrito: {data}")
        
        variant_id = data.get('variant_id')
        if variant_id and not isinstance(variant_id, (int, str)) or (isinstance(variant_id, str) and not variant_id.isdigit()):
            logger.error(f"ID de variante inválido: {variant_id}")
            return JsonResponse({'success': False, 'message': 'ID de variante inválido'}, status=400)
        
        try:
            quantity = int(data.get('quantity', 1))
            if quantity <= 0:
                logger.error("La cantidad debe ser mayor a 0.")
                return JsonResponse({'success': False, 'message': 'La cantidad debe ser mayor a 0.'}, status=400)
        except (ValueError, TypeError):
            logger.error(f"Cantidad inválida: {data.get('quantity')}")
            return JsonResponse({'success': False, 'message': 'Cantidad inválida'}, status=400)

        product = get_object_or_404(Product, id=product_id, available=True)
        logger.info(f"Producto encontrado: {product}")
        
        variant = None
        if variant_id:
            try:
                variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
                logger.info(f"Variante encontrada: {variant}")
            except Exception as e:
                logger.error(f"Error al obtener variante {variant_id}: {e}")
                return JsonResponse({'success': False, 'message': 'Variante no encontrada'}, status=404)

        stock = float('inf')
        if variant and hasattr(variant, 'stock') and variant.stock is not None:
            stock = variant.stock
            
        if quantity > stock:
            logger.warning(f"Cantidad solicitada ({quantity}) excede el stock disponible ({stock})")
            return JsonResponse({
                'success': False, 
                'message': f'Solo hay {stock} unidades disponibles de este producto'
            }, status=400)

        if variant:
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant)
        else:
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=None)

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
            
        cart_item.selected = True
        cart_item.save()

        logger.info(f"Producto agregado al carrito: {cart_item}")
        
        if request.headers.get('HX-Request'):
            from django.middleware.csrf import get_token
            total = cart.get_final_total()
            response = render(request, 'cart/cart_partial.html', {
                'cart': cart,
                'total': total,
                'csrf_token': get_token(request),
            })
            response['X-Cart-Total'] = str(total)
            response['X-Trigger-Cart-Update'] = 'true'
            return response
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            total = cart.get_final_total()
            return JsonResponse({
                'success': True,
                'message': 'Producto agregado al carrito',
                'total_items': cart.items.count(),
                'total': str(total),
            })
        else:
            return redirect('cart:cart_detail')
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}")
        return JsonResponse({'success': False, 'message': 'Error en los datos enviados.'}, status=400)
    except Exception as e:
        logger.error(f"Error inesperado al agregar al carrito: {e}")
        return JsonResponse({'success': False, 'message': 'Error al agregar el producto al carrito. Intente nuevamente.'}, status=500)

@login_required
@never_cache
def cart_detail(request):
    cart = get_or_create_cart(request)
    cart_items = list(cart.items.select_related('product'))
    
    if not cart_items:
        messages.info(request, "Tu carrito está vacío.")
        return render(request, 'cart/detail.html', {
            'cart': cart,
            'total': cart.get_final_total(),
            'suggestions': Product.objects.none()
        })
    
    # Una sola query para saber qué productos han sido comprados por el usuario
    product_ids = [item.product_id for item in cart_items]
    purchased_ids = set(
        OrderItem.objects.filter(
            product_id__in=product_ids,
            order__user=request.user,
            order__paid=True
        ).values_list('product_id', flat=True)
    ) if request.user.is_authenticated else set()
    
    for item in cart_items:
        item.user_has_purchased = item.product_id in purchased_ids
    
    # Sugerencias aleatorias sin ORDER BY RAND()
    import random
    all_exclude_ids = product_ids
    suggestion_ids = list(Product.objects.filter(available=True).exclude(
        id__in=all_exclude_ids
    ).values_list('id', flat=True)[:100])
    selected_ids = random.sample(suggestion_ids, min(3, len(suggestion_ids))) if suggestion_ids else []
    suggestions = Product.objects.filter(
        id__in=selected_ids
    ).select_related('brand') if selected_ids else Product.objects.none()
    
    return render(request, 'cart/detail.html', {
        'cart': cart,
        'total': cart.get_final_total(),
        'suggestions': suggestions,
        'breadcrumbs': [{'label': 'Carrito', 'url': None}],
    })

@require_GET
@never_cache
def get_suggestions(request):
    cart = get_or_create_cart(request)
    product_ids = [item.product_id for item in cart.items.all()]
    suggestion_ids = list(Product.objects.filter(available=True).exclude(
        id__in=product_ids
    ).values_list('id', flat=True)[:100])
    import random
    selected_ids = random.sample(suggestion_ids, min(3, len(suggestion_ids))) if suggestion_ids else []
    suggestions = Product.objects.filter(id__in=selected_ids).select_related('brand') if selected_ids else Product.objects.none()
    return render(request, 'cart/suggestions_partial.html', {'suggestions': suggestions})

@require_http_methods(["DELETE"])
def remove_item(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    total = cart.get_final_total()
    if request.headers.get('HX-Request'):
        from django.middleware.csrf import get_token
        csrf_token = get_token(request)
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
def increase_quantity(request, item_id):
    try:
        cart = get_or_create_cart(request)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        if item.variant:
            stock = item.variant.stock if hasattr(item.variant, 'stock') and item.variant.stock is not None else float('inf')
        else:
            stock = item.product.stock if hasattr(item.product, 'stock') and item.product.stock is not None else float('inf')
        if item.quantity < stock:
            item.quantity += 1
            item.save()
        else:
            messages.warning(request, f"No se puede aumentar la cantidad. Solo hay {stock} unidades disponibles.")
        total = cart.get_final_total()
        if request.headers.get('HX-Request'):
            from django.middleware.csrf import get_token
            csrf_token = get_token(request)
            response = render(request, 'cart/cart_partial.html', {
                'cart': cart,
                'total': total,
                'csrf_token': csrf_token,
            })
            response['X-Cart-Total'] = str(total)
            response['X-Trigger-Cart-Update'] = 'true'
            return response
        return HttpResponse(status=204)
    except Exception as e:
        logger.error(f"Error en increase_quantity item_id={item_id}: {e}")
        if request.headers.get('HX-Request'):
            return HttpResponse(f"<div class='text-red-500 p-4'>Error al actualizar cantidad: {str(e)}</div>", status=500)
        return JsonResponse({'success': False, 'message': 'Error al actualizar la cantidad.'}, status=500)

@require_POST
def decrease_quantity(request, item_id):
    try:
        cart = get_or_create_cart(request)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            messages.info(request, "La cantidad mínima es 1. Si desea eliminar el producto, use el botón de eliminar.")
        total = cart.get_final_total()
        if request.headers.get('HX-Request'):
            from django.middleware.csrf import get_token
            csrf_token = get_token(request)
            response = render(request, 'cart/cart_partial.html', {
                'cart': cart,
                'total': total,
                'csrf_token': csrf_token,
            })
            response['X-Cart-Total'] = str(total)
            response['X-Trigger-Cart-Update'] = 'true'
            return response
        return HttpResponse(status=204)
    except Exception as e:
        logger.error(f"Error en decrease_quantity item_id={item_id}: {e}")
        if request.headers.get('HX-Request'):
            return HttpResponse(f"<div class='text-red-500 p-4'>Error al actualizar cantidad: {str(e)}</div>", status=500)
        return JsonResponse({'success': False, 'message': 'Error al actualizar la cantidad.'}, status=500)

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
    stock = float('inf')
    if item.variant and hasattr(item.variant, 'stock') and item.variant.stock is not None:
        stock = item.variant.stock
    if new_quantity > stock:
        messages.warning(request, f"Solo hay {stock} unidades disponibles de este producto.")
        new_quantity = stock
    item.quantity = max(1, new_quantity)
    item.save()
    total = cart.get_final_total()
    if request.headers.get('HX-Request'):
        from django.middleware.csrf import get_token
        csrf_token = get_token(request)
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
    
    # Verificar si es una solicitud AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        # Devolver JSON para solicitudes AJAX
        return JsonResponse({
            'total_items': cart.get_total_items(),
            'total_price': float(total),
            'shipping_cost': float(cart.shipping_cost),
            'shipping_discount': float(cart.shipping_discount)
        })
    else:
        # Devolver HTML para solicitudes normales
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


def get_cart_count(request):
    """Endpoint AJAX que devuelve el conteo del carrito en JSON."""
    try:
        cart = get_or_create_cart(request)
        count = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    except Exception:
        count = 0
    return JsonResponse({'count': count})
