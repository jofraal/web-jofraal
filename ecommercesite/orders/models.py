from django.db import models
from products.models import Product, ProductVariant
from django.conf import settings
from coupons.models import Coupon
from decimal import Decimal
import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    DOCUMENT_TYPE_CHOICES = [
        ('DNI', 'DNI'),
        ('RUC', 'RUC'),
        ('CE', 'Carnet de Extranjería'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES, blank=True, null=True)
    document_number = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=20)
    department = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=20, decimal_places=16, blank=True, null=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=16, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    street_number = models.CharField(max_length=10, blank=True, null=True)
    additional_info = models.CharField(max_length=250, blank=True, null=True)
    map_image = models.ImageField(upload_to='map_images/', blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invoice_requested = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=20, blank=True, null=True)
    payment_preference_id = models.CharField(max_length=100, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey(Coupon, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    discount = models.IntegerField(default=0)
    coupon_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    external_reference = models.CharField(max_length=100, unique=True, blank=True, null=True)
    request_token = models.CharField(max_length=36, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'orders_order'
        managed = True
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'

    def clean(self):
        if self.address and self.address.lower() == 'pendiente':
            raise ValidationError({'address': 'La dirección no puede ser "Pendiente".'})

    def save(self, *args, **kwargs):
        self.full_clean()  # Ejecuta clean() antes de guardar
        super().save(*args, **kwargs)

    def get_total_cost(self):
        try:
            total = sum(item.get_cost() for item in self.items.all())
            return Decimal(str(total)).quantize(Decimal('0.01'))
        except Exception as e:
            logger.error(f"Error en get_total_cost: {e}")
            return Decimal('0.01')
        
    def get_total_with_discount(self):
        try:
            total = self.get_total_cost()
            coupon_discount = Decimal(str(self.coupon_discount_amount)).quantize(Decimal('0.01'))
            result = max(Decimal('0.01'), total - coupon_discount)
            return result.quantize(Decimal('0.01'))
        except Exception as e:
            logger.error(f"Error en get_total_with_discount: {e}")
            return Decimal('0.01')
            
    def get_final_total(self):
        try:
            subtotal = self.get_total_with_discount()
            shipping_cost = Decimal(str(self.shipping_cost)).quantize(Decimal('0.01'))
            shipping_discount = Decimal(str(self.shipping_discount)).quantize(Decimal('0.01'))
            effective_shipping = max(Decimal('0'), shipping_cost - shipping_discount)
            final_total = subtotal + effective_shipping
            return max(Decimal('0.01'), final_total).quantize(Decimal('0.01'))
        except Exception as e:
            logger.error(f"Error en get_final_total: {e}")
            return Decimal('0.01')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    variant_info = models.CharField(max_length=255, blank=True, null=True)

    def get_cost(self):
        try:
            price_decimal = Decimal(str(self.price)).quantize(Decimal('0.01'))
            quantity_decimal = Decimal(str(self.quantity))
            return (price_decimal * quantity_decimal).quantize(Decimal('0.01'))
        except Exception as e:
            logger.error(f"Error en OrderItem.get_cost: {e}")
            return Decimal('0.01')
