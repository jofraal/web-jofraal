from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse, HttpResponseServerError
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
import mercadopago
from products.models import Product, Brand, Category
from .forms import ReclamacionForm
from .models import Reclamacion, NewsletterSubscriber
from django.utils.html import strip_tags

# Vista para la página principal (home)
def home(request):
    brands = Brand.objects.all().only('id', 'name', 'logo')
    
    # Obtener categorías y agrupar productos en 2 queries en vez de N+1
    categories = list(Category.objects.all())
    category_slugs = [c.slug for c in categories]
    
    # Una sola query para todos los productos de todas las categorías
    all_products = list(Product.objects.filter(
        available=True,
        category__slug__in=category_slugs
    ).select_related('category', 'brand').order_by('-created')[:50])
    
    # Agrupar en Python (gratis, sin queries extra)
    category_products = {}
    for product in all_products:
        cat_name = product.category.name
        if cat_name not in category_products:
            category_products[cat_name] = []
        if len(category_products[cat_name]) < 3:
            category_products[cat_name].append(product)
    
    categories_list = [
        {'name': c.name, 'slug': c.slug}
        for c in categories if c.name in category_products
    ]
    
    context = {
        'is_home_page': True,
        'category_products': category_products,
        'brands': brands,
        'categories': categories_list,
    }
    return render(request, 'core/home.html', context)

# Vista para crear una preferencia de pago con Mercado Pago (legacy/dummy)
def create_payment_preference(request):
    try:
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        preference_data = {
            "items": [
                {
                    "title": "Producto Ejemplo",
                    "quantity": 1,
                    "unit_price": 100.0,
                    "currency_id": "PEN",
                }
            ],
            "back_urls": {
                "success": request.build_absolute_uri('/orders/success/'),
                "failure": request.build_absolute_uri('/orders/failure/'),
                "pending": request.build_absolute_uri('/orders/pending/'),
            },
            "auto_return": "all",
        }
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        return JsonResponse({"id": preference["id"]})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en create_payment_preference: {e}")
        return JsonResponse({"error": "Error al crear preferencia de pago"}, status=500)

# Vistas legacy para resultados de pago — redirigen a las de orders
def payment_success(request):
    return redirect('orders:payment_success')

def payment_failure(request):
    return redirect('orders:payment_failure')

def payment_pending(request):
    return redirect('orders:payment_pending')

# Vista para el formulario de reclamaciones
def complaint_form(request):
    if request.method == 'POST':
        form = ReclamacionForm(request.POST)
        if form.is_valid():
            reclamacion = form.save(commit=False)
            reclamacion.descripcion = strip_tags(reclamacion.descripcion)  # Sanitizar entrada
            reclamacion.save()
            return redirect('core:complaint_success', reclamacion_id=reclamacion.id)
    else:
        form = ReclamacionForm()
    return render(request, 'core/legal/complaint_form.html', {'form': form})

# Vista para mostrar el éxito de la reclamación
def complaint_success(request, reclamacion_id):
    reclamacion = get_object_or_404(Reclamacion, id=reclamacion_id)
    return render(request, 'core/legal/complaint_success.html', {
        'numero_correlativo': reclamacion.numero_correlativo,
        'reclamacion': reclamacion,
    })

# Vistas para las páginas legales
def terms(request):
    return render(request, 'core/legal/terms.html')

def privacy(request):
    return render(request, 'core/legal/privacy.html')

def preguntas_frecuentes(request):
    return render(request, 'core/soporte/preguntas_frecuentes.html')

def tiempos_costos_envio(request):
    return render(request, 'core/soporte/tiempos_costos_envio.html')

def formas_pago(request):
    return render(request, 'core/soporte/formas_pago.html')

def politica_cambios_devoluciones(request):
    return render(request, 'core/soporte/politica_cambios_devoluciones.html')

# Vista para la suscripción a la newsletter
@require_POST
def subscribe_newsletter(request):
    email = request.POST.get('email')
    if not email:
        return JsonResponse({'success': False, 'message': 'El correo electrónico es requerido.'}, status=400)

    try:
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created:
            return JsonResponse({'success': True, 'message': '¡Gracias por suscribirte a nuestra newsletter!'})
        else:
            return JsonResponse({'success': False, 'message': 'Tu correo ya ha sido registrado.'}, status=400)
    except ValidationError:
        return JsonResponse({'success': False, 'message': 'Por favor, ingresa un correo electrónico válido.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Ocurrió un error. Por favor, intenta de nuevo.'}, status=500)

# Vista para manejar errores globales
def custom_error_500(request):
    return HttpResponseServerError("Ocurrió un error en el servidor. Por favor, intenta más tarde.")