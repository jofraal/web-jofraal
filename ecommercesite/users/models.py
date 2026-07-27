from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    DOCUMENT_CHOICES = [
        ('DNI', 'DNI'),
        ('CE', 'Carnet de Extranjería'),
        ('Pasaporte', 'Pasaporte')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_CHOICES, blank=True, null=True)
    document_number = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return f'Perfil de {self.user.username}'

class Address(models.Model):
    ADDRESS_TYPE_CHOICES = (
        ('home', 'Casa'),
        ('work', 'Trabajo'),
        ('other', 'Otro'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    # Campo address_type ahora es opcional pero se mantiene para compatibilidad
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='home', blank=True, null=True, verbose_name='Tipo de dirección')
    
    # Campos de ubicación en Perú
    department = models.CharField(max_length=100, verbose_name='Departamento', default='Lima')
    province = models.CharField(max_length=100, verbose_name='Provincia', default='Lima')
    district = models.CharField(max_length=100, verbose_name='Distrito', default='Lima')
    
    # Campos de dirección detallada
    street = models.CharField(max_length=100, verbose_name='Calle/Avenida', default='')
    street_number = models.CharField(max_length=50, verbose_name='Número/Lote/Dpto', default='')
    additional_info = models.TextField(blank=True, null=True, verbose_name='Información Adicional')
    # Campo recipient ahora es opcional pero se mantiene para compatibilidad
    recipient = models.CharField(max_length=100, verbose_name='Destinatario', default='', blank=True, null=True)
    
    # Campos adicionales
    # Campo country ahora es opcional pero se mantiene para compatibilidad
    country = models.CharField(max_length=100, default='Perú', verbose_name='País', blank=True, null=True)
    is_default = models.BooleanField(default=False, verbose_name='Dirección Predeterminada')
    
    # Mantener campos de coordenadas para compatibilidad con código existente
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dirección'
        verbose_name_plural = 'Direcciones'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.get_address_type_display()} - {self.department}, {self.province}, {self.district}, {self.street} {self.street_number}"
    
    # Para mantener compatibilidad con código existente que use el campo address
    @property
    def address(self):
        return f"{self.street} {self.street_number}, {self.district}, {self.province}, {self.department}"
    
    # Para mantener compatibilidad con código existente que use el campo city
    @property
    def city(self):
        return self.district
    
    # Para mantener compatibilidad con código existente que use el campo state
    @property
    def state(self):
        return self.province
    
    def save(self, *args, **kwargs):
        # Si esta dirección se marca como predeterminada, desmarcar las demás
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        
        # Si es la primera dirección del usuario, marcarla como predeterminada
        if not self.pk and not Address.objects.filter(user=self.user).exists():
            self.is_default = True
            
        # Limitar a 3 direcciones por usuario
        if not self.pk and Address.objects.filter(user=self.user).count() >= 3:
            raise ValueError("No se pueden agregar más de 3 direcciones por usuario.")
            
        super().save(*args, **kwargs)