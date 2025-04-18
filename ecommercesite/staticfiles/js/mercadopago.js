// static/js/mercadopago.js
const mp = new MercadoPago('TU_PUBLIC_KEY', {
    locale: 'es-AR'
});

document.getElementById('checkout-btn').addEventListener('click', function () {
    fetch('/cart/create-payment/')
        .then(response => response.json())
        .then(data => {
            mp.bricks().create('wallet', 'wallet-container', {
                initialization: {
                    preferenceId: data.id
                }
            });
        })
        .catch(error => console.error('Error al crear la preferencia:', error));
});