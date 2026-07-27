// mercadopago.js - Integración con Mercado Pago para el proceso de checkout

document.addEventListener('DOMContentLoaded', function() {
    // Evitar redeclaración de la variable MERCADOPAGO_PUBLIC_KEY
    // La variable ya está declarada en el HTML principal
    if (typeof window.MERCADOPAGO_PUBLIC_KEY === 'undefined') {
        console.error('Error: La clave pública de Mercado Pago no está definida');
        return;
    }

    // Inicializar el SDK de Mercado Pago
    const mp = new MercadoPago(window.MERCADOPAGO_PUBLIC_KEY, {
        locale: 'es-PE'
    });

    // Configurar el botón de pago
    const paymentButton = document.getElementById('payment-btn');
    if (!paymentButton) {
        console.warn('No se encontró el botón de pago en la página');
        return;
    }

    // Función para procesar el pago
    function procesarPago() {
        // Aquí deberías integrar la lógica real de pago con Mercado Pago
        console.log('Procesando pago con Mercado Pago...');
        // Lógica real: solicitar el punto de inicio de pago al backend y redirigir
        fetch('/orders/create-payment/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.init_point) {
                window.location.href = data.init_point;
            } else if (data.error) {
                alert('Error al procesar el pago: ' + data.error);
            } else {
                alert('Error inesperado al procesar el pago.');
            }
        })
        .catch(error => {
            console.error('Error en proceso de pago:', error);
            alert('Error al procesar el pago. Intente nuevamente.');
        });
    }

    paymentButton.addEventListener('click', function(e) {
        e.preventDefault();
        procesarPago();
    });

    // Exponer funciones al ámbito global para que puedan ser utilizadas por otros scripts
    window.mercadoPagoIntegration = {
        procesarPago: procesarPago,
        mp: mp
    };

    console.log('Integración con Mercado Pago inicializada correctamente');
});