from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # API endpoints para ubicaciones
    path('api/departments/', views.get_departments_api, name='get_departments'),
    path('api/provinces/', views.get_provinces_api, name='get_provinces'),
    path('api/districts/', views.get_districts_api, name='get_districts'),
    # API endpoints para datos de usuario
    path('api/user-data/', views.get_user_data_api, name='get_user_data'),
    path('api/user-addresses/', views.get_user_addresses_api, name='get_user_addresses'),
    # Endpoints para el proceso de checkout con múltiples pasos
    path("save-identification/", views.save_identification, name="save_identification"),
    path("save-shipping/", views.save_shipping, name="save_shipping"),
    path("save-session-data/", views.save_session_data, name="save_session_data"),
    # Rutas existentes
    path("confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
    path("delivery/", views.delivery_form, name="delivery_form"),
    path("create-payment/", views.create_payment, name="create_payment"),  # Cambiado de "payment/" a "create-payment/"
    path("success/", views.payment_success, name="payment_success"),
    path("failure/", views.payment_failure, name="payment_failure"),
    path("pending/", views.payment_pending, name="payment_pending"),
    path("checkout/", views.checkout, name="checkout"),
    # Rutas adicionales
    path("order-list/", views.order_list, name="order_list"),
    path("order-detail/<int:order_id>/", views.order_detail, name="order_detail"),
    path("mercadopago-webhook/", views.mercadopago_webhook, name="mercadopago_webhook"),
]
