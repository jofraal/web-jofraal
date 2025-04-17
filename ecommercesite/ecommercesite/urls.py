from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from products import views
from social_django import urls as social_urls  # Import social_django URLs

urlpatterns = [
    path('admin/', admin.site.urls),
    path("cart/", include('cart.urls')),
    path("orders/", include("orders.urls")),
    path('coupons/', include('coupons.urls', namespace='coupons')), # Añadir las URLs de cupones
    path('', include('core.urls', namespace='core')),
    path('product/', include('products.urls', namespace='products')),
    path('coleccion/', views.coleccion, name='coleccion'),
    path('users/', include('users.urls', namespace='users')),
    path('social/', include('social_django.urls', namespace='social_auth')),  # Cambia 'social' a 'social_auth'
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler500 = 'core.views.custom_error_500'