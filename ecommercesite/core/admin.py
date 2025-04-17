from django.contrib import admin
from .models import Reclamacion, NewsletterSubscriber

# Configuración para el modelo Reclamacion
@admin.register(Reclamacion)
class ReclamacionAdmin(admin.ModelAdmin):
    list_display = ('numero_correlativo', 'nombres', 'apellidos', 'fecha_hora', 'tipo_reclamo', 'tipo_solicitud')
    list_filter = ('tipo_reclamo', 'tipo_solicitud', 'fecha_hora')
    search_fields = ('nombres', 'apellidos', 'numero_documento', 'detalle')
    date_hierarchy = 'fecha_hora'
    ordering = ('-fecha_hora',)
    readonly_fields = ('fecha_hora', 'numero_correlativo', 'fecha_creacion', 'fecha_actualizacion')

# Configuración para el modelo NewsletterSubscriber
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    list_filter = ('subscribed_at',)
    search_fields = ('email',)
    date_hierarchy = 'subscribed_at'
    ordering = ('-subscribed_at',)
    readonly_fields = ('subscribed_at',)