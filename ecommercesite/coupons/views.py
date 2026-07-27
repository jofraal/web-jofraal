from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Coupon
from .forms import CouponApplyForm
from cart.models import Cart
from cart.views import get_or_create_cart
from django.contrib import messages
from django.urls import reverse


def _add_flash_messages_to_response(request, response):
    """Extrae mensajes flash del request y los agrega como headers de respuesta HTMX."""
    storage = messages.get_messages(request)
    flash_messages = []
    for message in storage:
        flash_messages.append({'message': str(message), 'type': message.level_tag})
    if flash_messages:
        last_message = flash_messages[-1]
        response['X-Flash-Message'] = last_message['message']
        response['X-Flash-Type'] = last_message['type']
    return response

@require_POST
def coupon_apply(request):
    now = timezone.now()
    cart = get_or_create_cart(request)
    form = CouponApplyForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data['code']
        try:
            coupon = Coupon.objects.get(
                code__iexact=code,
                valid_from__lte=now,
                valid_to__gte=now,
                active=True
            )
            # Verificar si el cupón ya está aplicado
            if cart.coupon == coupon:
                messages.info(request, f'El cupón "{coupon.code}" ya está aplicado.')
            # Verificar si el cupón es exclusivo y está asignado a otro usuario
            elif coupon.is_exclusive and request.user.is_authenticated and request.user != coupon.assigned_to:
                messages.error(request, f'El cupón "{coupon.code}" es exclusivo para otro usuario.')
            # Verificar si el usuario ya ha usado este cupón (solo para usuarios autenticados)
            elif request.user.is_authenticated and coupon.used_by.filter(id=request.user.id).exists():
                messages.error(request, f'El cupón "{coupon.code}" ya ha sido utilizado por tu cuenta.')
            else:
                cart.coupon = coupon
                cart.discount = coupon.discount # Guardar el porcentaje de descuento
                cart.save()
                messages.success(request, f'Cupón "{coupon.code}" aplicado correctamente.')
        except Coupon.DoesNotExist:
            messages.error(request, 'El cupón no es válido o ha expirado.')
    else:
        # Si el formulario no es válido (ej. campo vacío), mostrar error
        messages.error(request, 'Por favor, introduce un código de cupón.')

    # Si la solicitud es HTMX, devolver el resumen del carrito actualizado
    if request.headers.get('HX-Request'):
        # Calcular el total final para pasarlo al template
        total = cart.get_final_total()
        shipping_cost = cart.shipping_cost
        shipping_discount = cart.shipping_discount
        
        response = render(request, 'cart/cart_summary_partial.html', {
            'cart': cart,
            'total': total,
            'shipping_cost': shipping_cost,
            'shipping_discount': shipping_discount
        })
        
        response = _add_flash_messages_to_response(request, response)
        
        response['X-Cart-Total'] = str(total)
        response['X-Trigger-Cart-Update'] = 'true'
        return response
    else:
        return redirect('cart:cart_detail')

@require_POST
def coupon_remove(request):
    cart = get_or_create_cart(request)
    if cart.coupon:
        messages.success(request, f'Cupón "{cart.coupon.code}" eliminado.')
        cart.coupon = None
        cart.discount = 0
        cart.save()
    else:
        messages.info(request, 'No hay ningún cupón aplicado.')

    # Si la solicitud es HTMX, devolver el resumen del carrito actualizado
    if request.headers.get('HX-Request'):
        # Calcular el total final para pasarlo al template
        total = cart.get_final_total()
        shipping_cost = cart.shipping_cost
        shipping_discount = cart.shipping_discount
        
        response = render(request, 'cart/cart_summary_partial.html', {
            'cart': cart,
            'total': total,
            'shipping_cost': shipping_cost,
            'shipping_discount': shipping_discount
        })
        
        response = _add_flash_messages_to_response(request, response)
        
        response['X-Cart-Total'] = str(total)
        response['X-Trigger-Cart-Update'] = 'true'
        return response
    else:
        return redirect('cart:cart_detail')

