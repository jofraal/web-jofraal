from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # API endpoints para ubicaciones
    path('api/departments/', views.get_departments_api, name='get_departments'),
    path('api/provinces/', views.get_provinces_api, name='get_provinces'),
    path('api/districts/', views.get_districts_api, name='get_districts'),
    path("create/", views.order_create, name="order_create"),
    path("confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
    path("delivery/", views.delivery_form, name="delivery_form"),
    path("payment/", views.create_payment, name="create_payment"),
    path("success/", views.payment_success, name="payment_success"),
    path("failure/", views.payment_failure, name="payment_failure"),
    path("pending/", views.payment_pending, name="payment_pending"),
    path("checkout/", views.checkout, name="checkout"),
]
