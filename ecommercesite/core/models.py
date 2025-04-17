from django.db import models
from django.utils import timezone

class Reclamacion(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('dni', 'DNI'),
        ('ce', 'Carnet de Extranjería'),
        ('pasaporte', 'Pasaporte'),
    ]
    
    TIPO_RECLAMO_CHOICES = [
        ('reclamo', 'Reclamo (disconformidad relacionada a los productos o servicios)'),
        ('queja', 'Queja (disconformidad no relacionada a los productos o servicios; o, malestar o descontento respecto a la atención al público)'),
    ]
    
    TIPO_SOLICITUD_CHOICES = [
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
    ]
    
    # Datos automáticos
    fecha_hora = models.DateTimeField(default=timezone.now)
    numero_correlativo = models.CharField(max_length=20, unique=True)
    
    # Datos del cliente
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=15, choices=TIPO_DOCUMENTO_CHOICES)
    numero_documento = models.CharField(max_length=20)
    departamento = models.CharField(max_length=50)
    provincia = models.CharField(max_length=50)
    distrito = models.CharField(max_length=50)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=15)
    email = models.EmailField()
    representante = models.CharField(max_length=100, blank=True, null=True, 
                                     help_text="Padre o Madre / Representante (en el caso que usted sea menor de edad)")
    
    # Detalles de la solicitud
    tipo_solicitud = models.CharField(max_length=10, choices=TIPO_SOLICITUD_CHOICES, default='producto')
    numero_pedido = models.CharField(max_length=100)
    monto_reclamado = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Detalle de la reclamación
    tipo_reclamo = models.CharField(max_length=10, choices=TIPO_RECLAMO_CHOICES, default='reclamo')
    detalle = models.TextField()
    pedido = models.TextField()
    observaciones = models.TextField(blank=True, null=True, 
                                   help_text="Observaciones y acciones adoptadas por el proveedor")
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Reclamación #{self.numero_correlativo} - {self.nombres} {self.apellidos}"
    
    def save(self, *args, **kwargs):
        if not self.numero_correlativo:
            last_correlativo = Reclamacion.objects.order_by('-id').first()
            if last_correlativo:
                last_num = int(last_correlativo.numero_correlativo.split('-')[1])
                self.numero_correlativo = f"LR-{last_num + 1:06d}"
            else:
                self.numero_correlativo = "LR-000001"
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Reclamación"
        verbose_name_plural = "Reclamaciones"
        ordering = ['-fecha_creacion']

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True, max_length=255)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Suscriptor de Newsletter"
        verbose_name_plural = "Suscriptores de Newsletter"

    