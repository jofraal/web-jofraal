import logging
from users.models import Address
from decimal import Decimal
from .models import Order, OrderItem
from cart.models import Cart
from django.db import transaction

logger = logging.getLogger(__name__)


def reduce_stock_from_order(order):
    """
    Reduce el stock de las variantes/productos cuando se confirma un pago.
    Retorna (éxito, mensaje de error).
    """
    try:
        with transaction.atomic():
            for item in order.items.select_related('product', 'variant').all():
                if item.variant:
                    variant = item.variant
                    if variant.stock >= item.quantity:
                        variant.stock -= item.quantity
                        variant.save(update_fields=['stock'])
                        logger.info(f"Stock reducido: variante {variant.sku or variant.id} -{item.quantity} (nuevo: {variant.stock})")
                    else:
                        logger.error(f"Stock insuficiente para variante {variant.sku or variant.id}: tiene {variant.stock}, necesita {item.quantity}")
                        return False, f"Stock insuficiente para {item.product.name} - {variant.color}/{variant.size}"
                else:
                    product = item.product
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save(update_fields=['stock'])
                        logger.info(f"Stock reducido: producto {product.sku or product.id} -{item.quantity} (nuevo: {product.stock})")
                    else:
                        # Si el producto no tiene variantes, intentar stock a nivel producto
                        total_variant_stock = sum(v.stock for v in product.variants.all())
                        logger.error(f"Stock insuficiente para producto {product.sku or product.id}")
                        return False, f"Stock insuficiente para {item.product.name}"
            return True, None
    except Exception as e:
        logger.exception(f"Error al reducir stock para orden {order.id}: {e}")
        return False, str(e)


def restore_stock_from_order(order):
    """
    Restaura el stock cuando una orden se cancela o el pago falla.
    """
    try:
        with transaction.atomic():
            for item in order.items.select_related('product', 'variant').all():
                if item.variant:
                    item.variant.stock += item.quantity
                    item.variant.save(update_fields=['stock'])
                    logger.info(f"Stock restaurado: variante {item.variant.sku or item.variant.id} +{item.quantity}")
                elif hasattr(item.product, 'stock') and item.product.stock is not None:
                    item.product.stock += item.quantity
                    item.product.save(update_fields=['stock'])
                    logger.info(f"Stock restaurado: producto {item.product.sku or item.product.id} +{item.quantity}")
            return True
    except Exception as e:
        logger.exception(f"Error al restaurar stock para orden {order.id}: {e}")
        return False


def create_order_from_cart(cart, order_data, payment_data=None):
    """
    Crea una orden a partir del carrito, evitando duplicidad.
    Si ya existe una orden para el mismo carrito y usuario que no está pagada, la retorna.
    """
    try:
        # Buscar si ya existe una orden pendiente para este usuario y datos
        existing_order = Order.objects.filter(user=cart.user, paid=False, status='pending').first()
        if existing_order:
            logger.info(f"Orden existente encontrada para el usuario {cart.user}: {existing_order.id}")
            return existing_order

        # Procesar latitud y longitud para asegurar que no excedan los 16 decimales
        latitude = order_data.get('latitude')
        longitude = order_data.get('longitude')
        
        # Convertir a Decimal y redondear a 16 decimales si es necesario
        if latitude is not None and latitude != '':
            try:
                latitude = Decimal(str(latitude)).quantize(Decimal('0.0000000000000001'))
                logger.info(f"Latitud procesada para la orden: {latitude}")
            except Exception as e:
                logger.error(f"Error al procesar latitud: {e}")
                latitude = None
        
        if longitude is not None and longitude != '':
            try:
                longitude = Decimal(str(longitude)).quantize(Decimal('0.0000000000000001'))
                logger.info(f"Longitud procesada para la orden: {longitude}")
            except Exception as e:
                logger.error(f"Error al procesar longitud: {e}")
                longitude = None

        # Log específico para verificar los campos de documento
        logger.info(f"document_type en order_data: {order_data.get('document_type', 'NO ENCONTRADO')}")
        logger.info(f"document_number en order_data: {order_data.get('document_number', 'NO ENCONTRADO')}")
        logger.info(f"Todas las claves en order_data: {list(order_data.keys())}")

        # Crear nueva orden
        order = Order.objects.create(
            user=cart.user,
            first_name=order_data.get('first_name', ''),
            last_name=order_data.get('last_name', ''),
            email=order_data.get('email', ''),
            document_type=order_data.get('document_type', ''),
            document_number=order_data.get('document_number', ''),
            phone=order_data.get('phone', ''),
            department=order_data.get('department', ''),
            province=order_data.get('province', ''),
            district=order_data.get('district', ''),
            city=order_data.get('city', ''),
            latitude=latitude,
            longitude=longitude,
            address=order_data.get('address', ''),
            street=order_data.get('street', ''),
            street_number=order_data.get('street_number', ''),
            additional_info=order_data.get('additional_info', ''),
            country=order_data.get('country', 'PE'),
            invoice_requested=order_data.get('invoice_requested', False),
            shipping_cost=cart.shipping_cost,
            shipping_discount=cart.shipping_discount,
            coupon=cart.coupon,
            discount=cart.discount,
            coupon_discount_amount=cart.get_coupon_discount_amount(),
            total=cart.get_final_total(),
            payment_id=payment_data.get('payment_id') if payment_data else None,
            payment_status=payment_data.get('status') if payment_data else None,
            payment_preference_id=payment_data.get('preference_id') if payment_data else None,
            external_reference=payment_data.get('external_reference') if payment_data else None,
            request_token=payment_data.get('request_token') if payment_data else None,
        )
        # Crear los items de la orden
        for item in cart.items.filter(selected=True):
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                price=item.product.discounted_price if hasattr(item.product, 'discounted_price') else item.product.price,
                quantity=item.quantity,
                variant_info=str(item.variant) if item.variant else ''
            )
        # Logs para verificar los datos críticos antes de crear la orden
        logger.info(f"Datos recibidos para crear orden: latitude={order_data.get('latitude')}, longitude={order_data.get('longitude')}, payment_id={payment_data.get('payment_id') if payment_data else None}, payment_status={payment_data.get('status') if payment_data else None}, payment_preference_id={payment_data.get('preference_id') if payment_data else None}")
        
        
        # Verificar si hay datos de pago y actualizarlos si es necesario
        if payment_data and (payment_data.get('payment_id') or payment_data.get('preference_id') or payment_data.get('external_reference') or payment_data.get('request_token')):
            if payment_data.get('payment_id') and not order.payment_id:
                order.payment_id = payment_data.get('payment_id')
                logger.info(f"Actualizado payment_id: {order.payment_id}")
            
            if payment_data.get('status') and not order.payment_status:
                order.payment_status = payment_data.get('status')
                logger.info(f"Actualizado payment_status: {order.payment_status}")
                
            if payment_data.get('preference_id') and not order.payment_preference_id:
                order.payment_preference_id = payment_data.get('preference_id')
                logger.info(f"Actualizado payment_preference_id: {order.payment_preference_id}")
                
            if payment_data.get('external_reference') and not order.external_reference:
                order.external_reference = payment_data.get('external_reference')
                logger.info(f"Actualizado external_reference: {order.external_reference}")
                
            if payment_data.get('request_token') and not order.request_token:
                order.request_token = payment_data.get('request_token')
                logger.info(f"Actualizado request_token: {order.request_token}")
                
            order.save()
            logger.info(f"Orden actualizada con datos de pago: {order.id}")
        
        logger.info(f"Orden creada exitosamente: {order.id}")
        return order
    except Exception as e:
        logger.error(f"Error al crear la orden desde el carrito: {e}")
        raise