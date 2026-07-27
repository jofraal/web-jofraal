from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name='Código')
    valid_from = models.DateTimeField(verbose_name='Válido desde', default=timezone.now)
    valid_to = models.DateTimeField(verbose_name='Válido hasta', default=timezone.now)
    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Porcentaje de descuento (0-100)',
        verbose_name='Descuento (%)'
    )
    active = models.BooleanField(default=True, verbose_name='Activo')
    used_by = models.ManyToManyField(User, blank=True, related_name='used_coupons', verbose_name='Usado por')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='assigned_coupons',
        verbose_name='Asignado a usuario específico'
    )
    is_exclusive = models.BooleanField(default=False, verbose_name='Cupón exclusivo')

    class Meta:
        verbose_name = 'Cupón'
        verbose_name_plural = 'Cupones'
        ordering = ['-valid_to']

    def is_valid(self, user=None):
        """Check if the coupon is currently valid.
        If user is provided, also check if the coupon is valid for this specific user.
        """
        now = timezone.now()
        is_time_valid = self.active and self.valid_from <= now <= self.valid_to
        
        # Si el cupón no es válido por tiempo o estado, retornar False directamente
        if not is_time_valid:
            return False
            
        # Si el cupón es exclusivo, verificar que esté asignado al usuario correcto
        if self.is_exclusive and user is not None:
            return self.assigned_to == user
        
        return True

    def __str__(self):
        return self.code
