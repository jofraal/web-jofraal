from django.contrib import admin
from django.utils import timezone
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'valid_from', 'valid_to', 'active', 'is_valid_now']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']
    list_editable = ['discount', 'active']
    readonly_fields = ['is_valid_now']
    
    def is_valid_now(self, obj):
        now = timezone.now()
        # Verificar que valid_from y valid_to no sean None antes de comparar
        if obj.valid_from is None or obj.valid_to is None:
            return False
        is_valid = obj.active and obj.valid_from <= now <= obj.valid_to
        return is_valid
    
    is_valid_now.short_description = 'Válido ahora'
    is_valid_now.boolean = True
