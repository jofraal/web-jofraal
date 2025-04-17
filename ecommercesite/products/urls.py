from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Use Class-Based View for product list
    path('', views.ProductListView.as_view(), name='product_list'),
    path('category/<slug:category_slug>/', views.ProductListView.as_view(), name='product_list_by_category'),
    path('coleccion/', views.coleccion, name='coleccion'), # Keep FBV for now
    # Use Class-Based View for product detail
    path('<int:id>/<slug:slug>/', views.ProductDetailView.as_view(), name="product_detail"),
    path('gender/<str:gender>/', views.product_list_by_gender, name='product_list_by_gender'), # Keep FBV for now
    path('ajax/', views.product_list_ajax, name='product_list_ajax'), # Keep FBV for AJAX endpoint
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'), # Keep FBV for review submission
]
