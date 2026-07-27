from django.conf import settings
import json

def mercadopago_settings(request):
    """
    Agrega las configuraciones de Mercado Pago al contexto de todas las plantillas.
    Utiliza un enfoque más seguro para manejar la clave pública.
    """
    # Crear un objeto de configuración que será serializado a JSON
    # Esto evita exponer directamente la clave en el HTML
    config = {
        'payment_enabled': bool(settings.MERCADO_PAGO_PUBLIC_KEY and settings.MERCADO_PAGO_ACCESS_TOKEN),
    }
    
    # Incluir la clave pública solo en páginas relacionadas con pagos
    # Esto reduce la exposición de la clave en todas las páginas
    payment_pages = ['/cart/', '/checkout/', '/orders/']
    is_payment_page = hasattr(request, 'path') and any(page in request.path for page in payment_pages)
    
    if is_payment_page:
        config['public_key'] = settings.MERCADO_PAGO_PUBLIC_KEY
        return {
            'mercadopago_config': json.dumps(config),
            'MERCADO_PAGO_PUBLIC_KEY': settings.MERCADO_PAGO_PUBLIC_KEY,
        }
    
    return {
        'mercadopago_config': json.dumps(config),
    }