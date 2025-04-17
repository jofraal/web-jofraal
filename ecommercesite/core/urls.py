from django.urls import path
from . import views
from .views import create_payment_preference, payment_success, payment_failure, payment_pending

app_name = 'core'  # Namespace para las URLs de "core"

urlpatterns = [
    # Página de inicio
    path('', views.home, name='home'),
    
    # Rutas de Mercado Pago
    path('create-payment/', create_payment_preference, name='create_payment'),
    path('success/', payment_success, name='payment_success'),
    path('failure/', payment_failure, name='payment_failure'),
    path('pending/', payment_pending, name='payment_pending'),
    
    # Rutas legales agrupadas bajo /legal/
    path('legal/libro-reclamaciones/', views.complaint_form, name='complaint_form'),
    path('legal/reclamacion-exitosa/<int:reclamacion_id>/', views.complaint_success, name='complaint_success'),
    path('legal/terminos-y-condiciones/', views.terms, name='terms'),
    path('legal/politicas-de-privacidad/', views.privacy, name='privacy'),
    
    # Rutas de soporte agrupadas bajo /soporte/
    path('soporte/preguntas-frecuentes/', views.preguntas_frecuentes, name='preguntas_frecuentes'),
    path('soporte/tiempos-costos-envio/', views.tiempos_costos_envio, name='tiempos_costos_envio'),
    path('soporte/formas-pago/', views.formas_pago, name='formas_pago'),
    path('soporte/politica-cambios-devoluciones/', views.politica_cambios_devoluciones, name='politica_cambios_devoluciones'),
    
    # Ruta para el newsletter
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
]