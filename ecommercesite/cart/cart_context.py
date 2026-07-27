from .views import get_or_create_cart
from django.db.models import Sum

def cart_counter(request):
    """
    Agrega la cantidad de productos en el carrito al contexto de todas las plantillas.
    Usa agregación SQL en vez de iterar items en Python.
    """
    try:
        cart = get_or_create_cart(request)
        result = cart.items.aggregate(total=Sum('quantity'))
        cart_count = result['total'] or 0
    except Exception:
        cart_count = 0
        
    return {
        'cart_count': cart_count
    }