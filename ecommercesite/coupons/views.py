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
            else:
                cart.coupon = coupon
                cart.discount = coupon.discount # Guardar el porcentaje de descuento
                cart.save()
                messages.success(request, f'Cupón "{coupon.code}" aplicado correctamente.')
        except Coupon.DoesNotExist:
            # Si el cupón no existe o no es válido, quitar cualquier cupón existente
            if cart.coupon:
                 messages.info(request, f'Cupón "{cart.coupon.code}" eliminado.')
                 cart.coupon = None
                 cart.discount = 0
                 cart.save()
            messages.error(request, 'El cupón no es válido o ha expirado.')
    else:
        # Si el formulario no es válido (ej. campo vacío), mostrar error
        messages.error(request, 'Por favor, introduce un código de cupón.')

    # Si la solicitud es HTMX, devolver el resumen del carrito actualizado
    if request.headers.get('HX-Request'):
        response = render(request, 'cart/cart_summary_partial.html', {'cart': cart})
        # Añadir mensajes flash a las cabeceras de respuesta
        storage = messages.get_messages(request)
        flash_messages = []
        for message in storage:
            flash_messages.append({'message': str(message), 'type': message.level_tag})
        if flash_messages:
            # Usar el último mensaje para la cabecera (o podrías concatenarlos)
            last_message = flash_messages[-1]
            response['X-Flash-Message'] = last_message['message']
            response['X-Flash-Type'] = last_message['type']
        response['X-Trigger-Cart-Update'] = 'true' # Para actualizar otras partes si es necesario
        return response
    else:
        # Comportamiento original para solicitudes no HTMX
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
        response = render(request, 'cart/cart_summary_partial.html', {'cart': cart})
        # Añadir mensajes flash a las cabeceras de respuesta
        storage = messages.get_messages(request)
        flash_messages = []
        for message in storage:
            flash_messages.append({'message': str(message), 'type': message.level_tag})
        if flash_messages:
            last_message = flash_messages[-1]
            response['X-Flash-Message'] = last_message['message']
            response['X-Flash-Type'] = last_message['type']
        response['X-Trigger-Cart-Update'] = 'true'
        return response
    else:
        # Comportamiento original para solicitudes no HTMX
        return redirect('cart:cart_detail')
