from django.db import models
from products.models import Product
from django.conf import settings

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
    first_name = models.CharField(max_length=100, default='')
    last_name = models.CharField(max_length=150, default='')
    email = models.EmailField()
    # Estos campos están definidos pero no existen en la base de datos
    # Se marcan como no gestionados para evitar errores
    # Estos campos se manejan como propiedades Python, no como campos de base de datos
    _document_type = None
    _document_number = None
    
    @property
    def document_type(self):
        return self._document_type
        
    @document_type.setter
    def document_type(self, value):
        self._document_type = value
        
    @property
    def document_number(self):
        return self._document_number
        
    @document_number.setter
    def document_number(self, value):
        self._document_number = value
    phone = models.CharField(max_length=20)
    # Campos de envío
    department = models.CharField(max_length=100, blank=True)  # Departamento
    province = models.CharField(max_length=100, blank=True)  # Provincia
    district = models.CharField(max_length=100, blank=True)  # Distrito (obligatorio en el paso 2)
    city = models.CharField(max_length=100)  # Ciudad (campo requerido)
    address = models.CharField(max_length=250, blank=True)  # Dirección completa
    street = models.CharField(max_length=100, blank=True)  # Calle
    street_number = models.CharField(max_length=10, blank=True)  # Número
    additional_info = models.CharField(max_length=250, blank=True)  # Información adicional
    recipient = models.CharField(max_length=100, blank=True)  # Destinatario
    # Otros campos
    postal_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='Perú', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invoice_requested = models.BooleanField(default=False)

    class Meta:
        db_table = 'orders_order'
        managed = True

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    variant_info = models.CharField(max_length=255, blank=True, null=True)

    def get_cost(self):
        return self.price * self.quantity
