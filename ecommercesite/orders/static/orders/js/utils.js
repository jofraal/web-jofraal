// utils.js

/**
 * Sanitiza una entrada para prevenir XSS
 * @param {string} input - Valor de entrada
 * @returns {string}
 */
function sanitizeInput(input) {
    return input ? input.replace(/[<>]/g, '') : '';
}

/**
 * Obtiene el valor de una cookie
 * @param {string} name - Nombre de la cookie
 * @returns {string|null}
 */
function getCookie(name) {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith(`${name}=`))
        ?.split('=')[1];
    if (!cookieValue && name === 'csrftoken') {
        showNotification('Error de autenticación. Recarga la página.', 'error');
    }
    return cookieValue ? decodeURIComponent(cookieValue) : null;
}

/**
 * Muestra notificaciones al usuario
 * @param {string} message - Mensaje a mostrar
 * @param {string} [type=info] - Tipo de notificación (success, error, warning, info)
 */
function showNotification(message, type = 'info') {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'flex fixed top-4 right-4 z-50 flex-col gap-2';
        document.body.appendChild(container);
    }

    const notification = document.createElement('div');
    notification.className = 'p-4 max-w-md rounded-lg shadow-lg transition-all duration-300';

    const typeStyles = {
        success: 'bg-green-100 border-l-4 border-green-500 text-green-700',
        error: 'bg-red-100 border-l-4 border-red-500 text-red-700',
        warning: 'bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700',
        info: 'bg-blue-100 border-l-4 border-blue-500 text-blue-700'
    };

    notification.classList.add(...typeStyles[type].split(' '));
    notification.setAttribute('role', 'alert');

    notification.innerHTML = `
        <div class="flex justify-between items-center">
            <p class="text-sm font-medium">${sanitizeInput(message)}</p>
            <button type="button" class="text-gray-400 hover:text-gray-500" aria-label="Cerrar notificación">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
            </button>
        </div>
    `;

    container.appendChild(notification);

    const closeButton = notification.querySelector('button');
    closeButton.addEventListener('click', () => {
        notification.classList.add('opacity-0');
        setTimeout(() => notification.remove(), 300);
    });

    setTimeout(() => {
        notification.classList.add('opacity-0');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

/**
 * Valida correo electrónico
 * @param {string} email - Correo a validar
 * @returns {boolean}
 */
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Valida número de teléfono (9 dígitos)
 * @param {string} phone - Teléfono a validar
 * @returns {boolean}
 */
function isValidPhone(phone) {
    return !phone || /^[0-9]{9}$/.test(phone.replace(/\s+/g, ''));
}

/**
 * Formatea coordenadas con 7 decimales
 * @param {string|number} coordStr - Coordenada a formatear
 * @returns {number|null}
 */
function formatCoordinate(coordStr) {
    if (coordStr === null || coordStr === undefined) return null;
    const coordVal = String(coordStr).trim();
    if (coordVal === '') return null;
    const num = parseFloat(coordVal);
    if (isNaN(num)) return null;
    return parseFloat(num.toFixed(7));
}

/**
 * Aplica debouncing a eventos
 * @param {Function} func - Función a debouncer
 * @param {number} wait - Tiempo de espera en ms
 * @returns {Function}
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}