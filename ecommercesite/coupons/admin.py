from django.contrib import admin
from django.utils import timezone
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'valid_from', 'valid_to', 'active', 'is_exclusive', 'assigned_to_user', 'is_valid_now', 'usage_count']
    list_filter = ['active', 'valid_from', 'valid_to', 'is_exclusive']
    search_fields = ['code', 'assigned_to__username']
    list_editable = ['discount', 'active', 'is_exclusive']
    readonly_fields = ['is_valid_now', 'usage_count', 'used_by_users']
    filter_horizontal = ['used_by']
    fieldsets = [
        (None, {'fields': ['code', 'discount', 'valid_from', 'valid_to', 'active']}),
        ('Asignación exclusiva', {'fields': ['is_exclusive', 'assigned_to']}),
        ('Información de uso', {'fields': ['used_by', 'used_by_users', 'usage_count', 'is_valid_now']}),
    ]
    def is_valid_now(self, obj):
        now = timezone.now()
        # Verificar que valid_from y valid_to no sean None antes de comparar
        if obj.valid_from and obj.valid_to:
            return obj.active and obj.valid_from <= now <= obj.valid_to
        return False
    
    def usage_count(self, obj):
        return obj.used_by.count()
    
    def used_by_users(self, obj):
        users = obj.used_by.all()
        if not users:
            return "No utilizado por ningún usuario"
        return ", ".join([user.username for user in users])
    
    def assigned_to_user(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.username
        return "-"
    
    is_valid_now.short_description = 'Válido ahora'
    is_valid_now.boolean = True
    usage_count.short_description = 'Veces usado'
    used_by_users.short_description = 'Usado por'
    assigned_to_user.short_description = 'Asignado a'

