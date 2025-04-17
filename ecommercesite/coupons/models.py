from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name='Código')
    valid_from = models.DateTimeField(verbose_name='Válido desde')
    valid_to = models.DateTimeField(verbose_name='Válido hasta')
    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Porcentaje de descuento (0-100)',
        verbose_name='Descuento (%)'
    )
    active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Cupón'
        verbose_name_plural = 'Cupones'
        ordering = ['-valid_to']

    def is_valid(self):
        """Check if the coupon is currently valid."""
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

    def __str__(self):
        return self.code
