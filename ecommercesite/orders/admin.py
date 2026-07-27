from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import Order, OrderItem
import csv
import datetime
import uuid

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_full_name', 'email', 'get_document_info', 'get_address', 'created_at', 'updated_at', 'paid', 
                   'payment_id', 'payment_status', 'payment_preference_id', 'latitude', 'longitude', 'view_map']
    list_filter = ['paid', 'created_at', 'updated_at', 'status', 'payment_status', 'document_type']
    search_fields = ['first_name', 'last_name', 'email', 'address', 'document_number', 
                    'payment_id', 'payment_preference_id', 'external_reference', 'request_token']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at', 'map_preview']
    fieldsets = (
        (None, {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone', 'city')
        }),
        ('Identificación', {
            'fields': ('document_type', 'document_number')
        }),
        ('Dirección', {
            'fields': ('department', 'province', 'district', 'address', 'street', 'street_number', 
                      'additional_info', 'country', 'latitude', 'longitude', 'map_image')
        }),
        ('Pago', {
            'fields': ('paid', 'payment_id', 'payment_status', 'payment_preference_id', 
                      'external_reference', 'request_token')
        }),
        ('Detalles', {
            'fields': ('status', 'invoice_requested', 'total', 'shipping_cost', 'shipping_discount', 
                      'discount', 'coupon_discount_amount', 'coupon', 'created_at', 'updated_at')
        }),
        ('Vista previa', {
            'fields': ('map_preview',)
        }),
    )
    actions = ['export_to_csv', 'export_map_data']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Nombre completo'

    def get_address(self, obj):
        return obj.address or '-'
    get_address.short_description = 'Dirección'

    def get_document_info(self, obj):
        if obj.document_type and obj.document_number:
            return f"{obj.document_type}: {obj.document_number}"
        return '-'
    get_document_info.short_description = 'Documento de Identidad'

    def view_map(self, obj):
        if obj.latitude and obj.longitude:
            return format_html('<a href="https://www.google.com/maps?q={},{}" target="_blank">Ver mapa</a>', 
                              obj.latitude, obj.longitude)
        return '-'
    view_map.short_description = 'Mapa'

    def map_preview(self, obj):
        if obj.map_image:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', 
                              obj.map_image.url)
        elif obj.latitude and obj.longitude:
            google_maps_api_key = getattr(self.admin_site, 'google_maps_api_key', '')
            if not google_maps_api_key:
                from django.conf import settings
                google_maps_api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
            if google_maps_api_key:
                return format_html(
                    '<div style="margin-bottom: 10px;">' +
                    '<a href="https://www.google.com/maps?q={},{}" target="_blank" class="button">Abrir en Google Maps</a>' +
                    '</div>' +
                    '<div style="width: 100%; height: 400px; margin-bottom: 10px;">' +
                    '<iframe width="100%" height="100%" frameborder="0" style="border:0" ' +
                    'src="https://www.google.com/maps/embed/v1/place?key={}&q={},{}" allowfullscreen>' +
                    '</iframe></div>',
                    obj.latitude, obj.longitude, google_maps_api_key, obj.latitude, obj.longitude)
            return format_html(
                '<iframe width="200" height="200" frameborder="0" style="border:0" '
                'src="https://www.openstreetmap.org/export/embed.html?bbox={}%2C{}%2C{}%2C{}&layer=mapnik&marker={}%2C{}" allowfullscreen></iframe>',
                obj.longitude - 0.001, obj.latitude - 0.001, obj.longitude + 0.001, obj.latitude + 0.001, 
                obj.latitude, obj.longitude)
        return 'No hay datos de ubicación disponibles'
    map_preview.short_description = 'Vista previa del mapa'

    def export_to_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=orders_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])
        return response
    export_to_csv.short_description = 'Exportar a CSV'

    def export_map_data(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=map_data_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Dirección', 'Latitud', 'Longitud'])
        for obj in queryset:
            if obj.latitude and obj.longitude:
                writer.writerow([obj.id, f"{obj.first_name} {obj.last_name}", obj.address, obj.latitude, obj.longitude])
        return response
    export_map_data.short_description = 'Exportar datos de mapa'

    def save_model(self, request, obj, form, change):
        if not change:  # Solo para nuevas órdenes
            if not obj.external_reference:
                obj.external_reference = f"ORDER-{uuid.uuid4()}"
            if not obj.request_token:
                obj.request_token = str(uuid.uuid4())[:36]
            # Prevenir que address sea "Pendiente"
            if obj.address and obj.address.lower() == 'pendiente':
                obj.address = ''
        super().save_model(request, obj, form, change)
