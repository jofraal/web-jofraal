from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    shipping_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon = models.ForeignKey('coupons.Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='carts')
    discount = models.IntegerField(default=0)  # Porcentaje de descuento del cupón
    created = models.DateTimeField(auto_now_add=True)  # Campo para la fecha de creación
    updated = models.DateTimeField(auto_now=True)  # Campo para la fecha de última actualización

    def get_total_price(self):
        return sum(item.total_price() for item in self.items.all() if item.selected)

    def has_selected_items(self):
        return self.items.filter(selected=True).exists()

    def get_discount_amount(self):
        """Optimizado con agregación SQL en vez de iterar items en Python."""
        from django.db.models import Sum, F
        result = self.items.filter(selected=True).aggregate(
            total_original=Sum(F('quantity') * F('product__original_price'))
        )
        total_original = result['total_original'] or 0
        return total_original - self.get_total_price()

    def get_final_total(self):
        # Cachear el resultado para evitar recálculos en la misma request
        if hasattr(self, '_cached_final_total'):
            return self._cached_final_total
        try:
            # Asegurar que total_price sea Decimal
            total_price = Decimal(str(self.get_total_price())).quantize(Decimal('0.01'))
            
            # Si el total de la compra es mayor a 50 soles, el envío es gratis
            if total_price > Decimal('50'):
                self.shipping_discount = self.shipping_cost
            else:
                self.shipping_discount = Decimal('0')
            
            # Aplicar descuento del cupón si existe
            coupon_discount = Decimal('0')
            if self.coupon and self.discount > 0:
                try:
                    # Limitar el descuento al 99% del total para evitar montos negativos
                    max_discount_percentage = Decimal('99')
                    applied_discount = min(Decimal(str(self.discount)), max_discount_percentage)
                    coupon_discount = (total_price * applied_discount / Decimal('100')).quantize(Decimal('0.01'))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error al calcular descuento del cupón: {e}")
                    coupon_discount = Decimal('0')
            
            # Calcular el total final: Subtotal - Descuento por cupón + Envío efectivo
            shipping_cost_effective = max(Decimal('0'), self.shipping_cost - self.shipping_discount)
            
            # Asegurar que el total final sea al menos 0.01
            final_total = max(Decimal('0.01'), total_price - coupon_discount + shipping_cost_effective)
            self._cached_final_total = final_total.quantize(Decimal('0.01'))
            return self._cached_final_total
        except Exception as e:
            logger.error(f"Error en get_final_total: {e}")
            return Decimal('0.01')  # Valor mínimo en caso de error
        
    def get_total_items(self):
        """Retorna el número total de items en el carrito usando agregación SQL"""
        from django.db.models import Sum
        result = self.items.aggregate(total=Sum('quantity'))
        return result['total'] or 0
    
    def get_coupon_discount_amount(self):
        """Calcula el monto de descuento aplicado por el cupón"""
        if not self.coupon or self.discount <= 0:
            return Decimal('0.00')
        try:
            total_price = Decimal(str(self.get_total_price())).quantize(Decimal('0.01'))
            discount_decimal = Decimal(str(self.discount))
            return (total_price * discount_decimal / Decimal('100')).quantize(Decimal('0.01'))
        except (ValueError, TypeError) as e:
            logger.warning(f"Error al calcular monto de descuento del cupón: {e}")
            return Decimal('0.00')

    def all_items_selected(self):
        return self.items.exists() and not self.items.filter(selected=False).exists()

    def __str__(self):
        return f"Cart {self.id} - {'User: ' + str(self.user) if self.user else 'Anonymous'}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    selected = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['cart', 'product', 'variant']),
        ]

    def total_price(self):
        try:
            quantity_decimal = Decimal(str(self.quantity))
            
            if self.variant and self.variant.has_discount():
                price = Decimal(str(self.variant.get_price()))
            elif hasattr(self.product, 'discount_percentage') and self.product.discount_percentage > 0:
                price = Decimal(str(self.product.discounted_price))
            else:
                price = Decimal(str(self.product.price))
                
            return (quantity_decimal * price).quantize(Decimal('0.01'))
        except Exception as e:
            logger.error(f"Error en CartItem.total_price: {e}")
            # Devolver un valor mínimo en caso de error
            return Decimal('0.01')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.variant if self.variant else 'No variant'})"