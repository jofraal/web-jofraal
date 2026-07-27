from django.conf import settings

def google_maps_settings(request):
    """
    Context processor que hace disponible la clave API de Google Maps
    en todas las plantillas.
    """
    return {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }