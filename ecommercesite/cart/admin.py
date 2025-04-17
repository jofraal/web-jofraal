from django.contrib import admin
from .models import Cart, CartItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created', 'updated')  # Asegúrate de que 'created' y 'updated' existan en el modelo
    list_filter = ('created', 'updated')  # Asegúrate de que sean campos válidos en el modelo
    search_fields = ('user__username',)
    ordering = ('-created',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'variant', 'quantity')
    list_filter = ('product', 'variant')
    search_fields = ('product__name', 'variant__color', 'variant__size')
