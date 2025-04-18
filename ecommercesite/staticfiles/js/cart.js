document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault();
            const productId = button.getAttribute('data-product-id');
            const variantId = button.getAttribute('data-variant-id');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const response = await fetch(`/cart/add/${productId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ variant_id: variantId })
                });

                const data = await response.json();
                if (response.ok) {
                    alert(data.message);
                    // Update cart counter
                    const cartCounter = document.getElementById('cart-counter');
                    if (cartCounter) {
                        cartCounter.textContent = data.cart_count;
                    }
                } else {
                    alert(data.error || 'Ocurrió un error al agregar el producto al carrito.');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Ocurrió un error al procesar la solicitud.');
            }
        });
    });

    document.querySelectorAll('.remove-from-cart-btn').forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault();
            const itemId = button.getAttribute('data-item-id');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const response = await fetch(`/cart/remove/${itemId}/`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    }
                });

                const data = await response.json();
                if (response.ok) {
                    alert(data.message);
                    // Update cart counter
                    const cartCounter = document.getElementById('cart-counter');
                    if (cartCounter) {
                        cartCounter.textContent = data.cart_count;
                    }
                    // Reload cart container
                    document.getElementById('cart-container').innerHTML = data.html;
                } else {
                    alert(data.error || 'Ocurrió un error al eliminar el producto del carrito.');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Ocurrió un error al procesar la solicitud.');
            }
        });
    });
});
