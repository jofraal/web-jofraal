document.addEventListener('htmx:responseError', function (event) {
    // Solo mostrar el error si la URL contiene 'cart_add' y es realmente un error
    if (event.detail.xhr.responseURL.includes('cart_add')) {
        try {
            const response = JSON.parse(event.detail.xhr.responseText);
            if (response.message) {
                // Usar el sistema de notificaciones si está disponible
                if (window.notifications) {
                    window.notifications.error(response.message);
                } else {
                    alert(`Error: ${response.message}`);
                }
            } else {
                console.error('Error al agregar al carrito:', response);
            }
        } catch (e) {
            // Si no podemos analizar la respuesta como JSON, no mostramos nada
            console.error('Error al procesar la respuesta:', e);
        }
    }
});

document.addEventListener('htmx:afterSwap', function (event) {
    // Verificar si la operación fue exitosa basándose en los encabezados
    if (event.detail.xhr && event.detail.xhr.getResponseHeader('X-Trigger-Cart-Update') === 'true') {
        // Actualización exitosa del carrito
        console.log('Carrito actualizado correctamente');
        
        // Solo mostrar mensaje de éxito si la URL contiene 'cart_add'
        if (event.detail.xhr.responseURL && event.detail.xhr.responseURL.includes('cart_add')) {
            // Usar el sistema de notificaciones si está disponible
            if (window.notifications) {
                window.notifications.success('Producto agregado al carrito correctamente');
            } else {
                // Mostrar mensaje de éxito discreto como fallback
                const successMessage = document.createElement('div');
                successMessage.className = 'fixed top-4 right-4 z-50 p-4 text-white bg-green-500 rounded shadow-lg';
                successMessage.innerHTML = '<span>Producto agregado al carrito correctamente</span>';
                document.body.appendChild(successMessage);
                
                // Eliminar el mensaje después de 3 segundos
                setTimeout(() => {
                    successMessage.remove();
                }, 3000);
            }
            
            // Actualizar cualquier contador de carrito que pueda existir en la página
            updateCartCounters();
        }
    }
});

// Función para actualizar los contadores del carrito en la página
function updateCartCounters() {
    // Buscar elementos que muestren el contador del carrito
    const cartCounters = document.querySelectorAll('.cart-counter, .cart-badge');
    
    // Si hay contadores, hacer una solicitud para obtener el número actual de items
    if (cartCounters.length > 0) {
        fetch('/cart/get-summary/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.total_items !== undefined) {
                // Actualizar todos los contadores encontrados
                cartCounters.forEach(counter => {
                    counter.textContent = data.total_items;
                    
                    // Si el contador estaba oculto y hay items, mostrarlo
                    if (data.total_items > 0 && counter.classList.contains('hidden')) {
                        counter.classList.remove('hidden');
                    }
                    // Si no hay items, ocultar el contador
                    else if (data.total_items === 0 && !counter.classList.contains('hidden')) {
                        counter.classList.add('hidden');
                    }
                });
            }
        })
        .catch(error => console.error('Error al actualizar contador del carrito:', error));
    }
}
