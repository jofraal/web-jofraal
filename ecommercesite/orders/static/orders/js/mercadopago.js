/**
 * Script para manejar la integración con Mercado Pago
 * Versión mejorada con mejor manejo de errores y validaciones
 */
document.addEventListener('DOMContentLoaded', function () {
    // Verificar que la variable MERCADOPAGO_PUBLIC_KEY esté definida y no esté vacía
    if (typeof MERCADOPAGO_PUBLIC_KEY === 'undefined' || !MERCADOPAGO_PUBLIC_KEY) {
        console.error('Error: La clave pública de Mercado Pago no está definida o está vacía');
        // No mostrar alerta inmediatamente para no interrumpir la carga de la página
        return;
    }

    // Inicializar Mercado Pago con manejo de errores
    let mp;
    try {
        mp = new MercadoPago(MERCADOPAGO_PUBLIC_KEY, {
            locale: 'es-PE'
        });
        console.log('SDK de Mercado Pago inicializado correctamente');
    } catch (error) {
        console.error('Error al inicializar el SDK de Mercado Pago:', error);
        // Mostrar mensaje de error solo si el usuario intenta pagar
        const paymentBtn = document.getElementById('payment-btn');
        if (paymentBtn) {
            paymentBtn.addEventListener('click', function(e) {
                e.preventDefault();
                alert('Error al inicializar el sistema de pagos. Por favor, contacte al administrador.');
            });
        }
        return;
    }

    // Maneja la respuesta de HTMX cuando se crea un pago
    document.body.addEventListener('htmx:afterRequest', function (event) {
        // Verificar si la respuesta es del endpoint de creación de pago
        if (event.detail.xhr.responseURL.includes('/orders/payment/') || 
            event.detail.xhr.responseURL.includes('/orders/create_payment/')) {
            
            // Verificar si hay respuesta
            if (!event.detail.xhr.responseText) {
                console.error('Error: La respuesta del servidor está vacía');
                alert('Error: No se recibió respuesta del servidor. Por favor, intente nuevamente.');
                return;
            }

            try {
                // Parsear la respuesta JSON
                const response = JSON.parse(event.detail.xhr.responseText);
                console.log('Respuesta del servidor:', response);
                
                // Verificar si hay un ID de preferencia
                if (response.id) {
                    console.log('Preferencia de pago creada correctamente:', response.id);
                    
                    // Iniciar el checkout de Mercado Pago
                    mp.checkout({
                        preference: {
                            id: response.id
                        },
                        autoOpen: true
                    });
                } 
                // Verificar si hay un mensaje de error específico
                else if (response.error) {
                    console.error('Error del servidor:', response.error);
                    alert('Error: ' + response.error);
                } 
                // Respuesta inesperada
                else {
                    console.error('Respuesta inesperada del servidor:', response);
                    alert('No se pudo iniciar el pago. La respuesta del servidor no contiene un ID de preferencia.');
                }
            } catch (error) {
                // Error al procesar la respuesta JSON
                console.error('Error al procesar la respuesta del servidor:', error);
                alert('Hubo un error al procesar la respuesta del servidor. Por favor, inténtalo de nuevo.');
            }
        }
    });

    // Agregar evento para mostrar mensaje de carga al hacer clic en el botón de pago
    const paymentBtn = document.getElementById('payment-btn');
    if (paymentBtn) {
        paymentBtn.addEventListener('click', function() {
            // Solo mostrar mensaje si el botón no está deshabilitado
            if (!this.disabled) {
                // Cambiar el texto del botón para indicar que se está procesando
                const originalText = this.innerHTML;
                this.innerHTML = 'Procesando...';
                
                // Restaurar el texto original si hay un error (después de 10 segundos)
                setTimeout(() => {
                    if (this.innerHTML === 'Procesando...') {
                        this.innerHTML = originalText;
                    }
                }, 10000);
            }
        });
    }
});