from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),  # Ruta raíz del carrito
    path('home/', views.cart_detail, name='cart_home'),  # Alias para compatibilidad
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:item_id>/', views.remove_item, name='remove_item'),
    path('increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('update-quantity/<int:item_id>/', views.update_quantity, name='update_quantity'),
    path('toggle-select/<int:item_id>/', views.toggle_select, name='toggle_select'),
    path('toggle-select-all/', views.toggle_select_all, name='toggle_select_all'),
    path('get-suggestions/', views.get_suggestions, name='get_suggestions'),
    path('get-summary/', views.get_summary, name='get_summary'),
    path('create-payment/', views.create_payment, name='create_payment'),
    path('success/', views.payment_success, name='payment_success'),
    path('failure/', views.payment_failure, name='payment_failure'),
    path('pending/', views.payment_pending, name='payment_pending'),
]
