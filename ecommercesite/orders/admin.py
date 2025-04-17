from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_full_name', 'email', 'address', 'created_at', 'updated_at', 'paid']
    exclude = ['document_type', 'document_number']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at',]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Nombre completo'
