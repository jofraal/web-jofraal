# -*- coding: utf-8 -*-
"""
Vistas para el proceso de pago con integración mejorada de MercadoPago
Implementa las mejores prácticas para la validación de variables de entorno
y manejo de errores en la integración con MercadoPago.
"""

import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Importar utilidades de validación de entorno
from ..utils.env_validation import validate_mercadopago_config, get_client_env_context

# Configurar logger
logger = logging.getLogger(__name__)

def checkout_view(request):
    """
    Vista principal del proceso de checkout
    Incluye validación de variables de entorno y manejo de errores mejorado
    """
    # Validar configuración de MercadoPago
    mp_valid, missing_vars = validate_mercadopago_config()
    
    if not mp_valid:
        logger.error(f"Error en la configuración de MercadoPago. Variables faltantes: {', '.join(missing_vars)}")
        # Registrar el error pero permitir que la página se cargue
        # El script del cliente mostrará un mensaje de error si el usuario intenta pagar
    
    # Obtener contexto con variables de entorno para el cliente
    env_context = get_client_env_context()
    
    # Añadir variables adicionales al contexto
    context = {
        'page_title': 'Checkout',
        **env_context
    }
    
    return render(request, 'orders/checkout.html', context)

@require_POST
def save_session_data(request):
    """
    Guarda los datos de identificación y envío en la sesión
    """
    try:
        data = json.loads(request.body)
        
        # Guardar datos de identificación
        if 'identification_data' in data:
            request.session['identification_data'] = data['identification_data']
        
        # Guardar datos de envío
        if 'shipping_data' in data:
            request.session['shipping_data'] = data['shipping_data']
        
        return JsonResponse({'success': True})
    except json.JSONDecodeError:
        logger.error("Error al decodificar JSON en save_session_data")
        return JsonResponse({'success': False, 'error': 'Formato de datos inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error al guardar datos en la sesión: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def create_payment(request):
    """
    Crea una preferencia de pago en MercadoPago
    Implementa validación de variables de entorno y mejor manejo de errores
    """
    # Validar configuración de MercadoPago
    mp_valid, missing_vars = validate_mercadopago_config()
    
    if not mp_valid:
        error_msg = f"Error en la configuración de MercadoPago. Variables faltantes: {', '.join(missing_vars)}"
        logger.error(error_msg)
        return JsonResponse({'error': 'Error de configuración del servidor. Contacte al administrador.'}, status=500)
    
    try:
        # Obtener datos de la sesión
        identification_data = request.session.get('identification_data', {})
        shipping_data = request.session.get('shipping_data', {})
        
        # Validar datos mínimos necesarios
        if not identification_data.get('email'):
            return JsonResponse({'error': 'Falta el correo electrónico'}, status=400)
        
        # Aquí iría la lógica para crear la preferencia de pago en MercadoPago
        # Este es solo un ejemplo simplificado
        
        # Simular respuesta exitosa (en producción, esto vendría de la API de MercadoPago)
        return JsonResponse({
            'id': 'TEST_PREFERENCE_ID',
            'init_point': 'https://www.mercadopago.com.pe/checkout/v1/redirect?pref_id=TEST_PREFERENCE_ID'
        })
        
    except Exception as e:
        logger.error(f"Error al crear preferencia de pago: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def payment_webhook(request):
    """
    Webhook para recibir notificaciones de pago de MercadoPago
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Validar configuración de MercadoPago
        mp_valid, _ = validate_mercadopago_config()
        
        if not mp_valid:
            logger.error("Error en la configuración de MercadoPago al procesar webhook")
            return JsonResponse({'error': 'Error de configuración'}, status=500)
        
        # Procesar la notificación
        data = json.loads(request.body)
        logger.info(f"Notificación de pago recibida: {data}")
        
        # Aquí iría la lógica para procesar la notificación
        # Este es solo un ejemplo simplificado
        
        return JsonResponse({'status': 'ok'})
        
    except json.JSONDecodeError:
        logger.error("Error al decodificar JSON en webhook")
        return JsonResponse({'error': 'Formato de datos inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error al procesar webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)