from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

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
        total_original = sum(item.quantity * item.product.original_price for item in self.items.all() if item.selected)
        total_with_discount = self.get_total_price()
        return total_original - total_with_discount

    def get_final_total(self):
        total_price = self.get_total_price()
        # Si el total de la compra es mayor a 50 soles, el envío es gratis
        if total_price > 50:
            self.shipping_discount = self.shipping_cost
        else:
            self.shipping_discount = 0
            
        # Aplicar descuento del cupón si existe
        coupon_discount = 0
        if self.coupon and self.discount > 0:
            coupon_discount = (total_price * Decimal(self.discount) / Decimal(100)).quantize(Decimal('0.01'))
            
        return total_price - coupon_discount + self.shipping_cost - self.shipping_discount
        
    def get_coupon_discount_amount(self):
        """Calcula el monto de descuento aplicado por el cupón"""
        if not self.coupon or self.discount <= 0:
            return Decimal('0.00')
        return (self.get_total_price() * Decimal(self.discount) / Decimal(100)).quantize(Decimal('0.01'))

    def all_items_selected(self):
        return self.items.exists() and all(item.selected for item in self.items.all())

    def __str__(self):
        return f"Cart {self.id} - {'User: ' + str(self.user) if self.user else 'Anonymous'}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    selected = models.BooleanField(default=True)

    def total_price(self):
        if self.variant and self.variant.has_discount():
            return self.quantity * self.variant.get_price()
        elif self.product.discount_percentage > 0:
            return self.quantity * self.product.discounted_price
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.variant if self.variant else 'No variant'})"