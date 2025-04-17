/**
 * Sistema de notificaciones mejorado para la tienda virtual
 */

class NotificationSystem {
    constructor() {
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.style.position = 'fixed';
        this.container.style.top = '20px';
        this.container.style.right = '20px';
        this.container.style.zIndex = '1000';
        document.body.appendChild(this.container);
        
        this.notifications = [];
        this.maxNotifications = 3;
    }
    
    /**
     * Muestra una notificación
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo de notificación: 'success', 'error', 'info'
     * @param {Object} options - Opciones adicionales
     */
    show(message, type = 'info', options = {}) {
        const defaults = {
            title: this._getDefaultTitle(type),
            duration: 5000,
            closable: true,
        };
        
        const settings = {...defaults, ...options};
        
        // Crear el elemento de notificación
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.setAttribute('role', 'alert');
        
        // Agregar icono según el tipo
        const iconHtml = this._getIconForType(type);
        
        // Construir el contenido
        notification.innerHTML = `
            <div class="notification-icon">${iconHtml}</div>
            <div class="notification-content">
                <div class="notification-title">${settings.title}</div>
                <div class="notification-message">${message}</div>
            </div>
            ${settings.closable ? '<button class="notification-close" aria-label="Cerrar">&times;</button>' : ''}
        `;
        
        // Agregar al contenedor
        this.container.appendChild(notification);
        
        // Agregar a la lista de notificaciones activas
        const notificationData = { element: notification, timerId: null };
        this.notifications.push(notificationData);
        
        // Limitar el número de notificaciones visibles
        this._limitNotifications();
        
        // Configurar el cierre automático
        if (settings.duration > 0) {
            notificationData.timerId = setTimeout(() => {
                this._removeNotification(notification);
            }, settings.duration);
        }
        
        // Configurar el botón de cierre
        if (settings.closable) {
            const closeButton = notification.querySelector('.notification-close');
            closeButton.addEventListener('click', () => {
                this._removeNotification(notification);
            });
        }
        
        return notification;
    }
    
    /**
     * Muestra una notificación de éxito
     */
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }
    
    /**
     * Muestra una notificación de error
     */
    error(message, options = {}) {
        return this.show(message, 'error', options);
    }
    
    /**
     * Muestra una notificación informativa
     */
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
    
    /**
     * Elimina una notificación con animación
     */
    _removeNotification(notification) {
        // Buscar el índice de la notificación
        const index = this.notifications.findIndex(item => item.element === notification);
        if (index === -1) return;
        
        // Limpiar el temporizador si existe
        if (this.notifications[index].timerId) {
            clearTimeout(this.notifications[index].timerId);
        }
        
        // Agregar clase para animación de salida
        notification.classList.add('hiding');
        
        // Eliminar después de la animación
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            this.notifications.splice(index, 1);
        }, 300); // Duración de la animación
    }
    
    /**
     * Limita el número de notificaciones visibles
     */
    _limitNotifications() {
        if (this.notifications.length > this.maxNotifications) {
            const oldest = this.notifications[0].element;
            this._removeNotification(oldest);
        }
    }
    
    /**
     * Obtiene el título predeterminado según el tipo
     */
    _getDefaultTitle(type) {
        switch (type) {
            case 'success': return '¡Éxito!';
            case 'error': return 'Error';
            case 'info': return 'Información';
            default: return 'Notificación';
        }
    }
    
    /**
     * Obtiene el icono HTML según el tipo
     */
    _getIconForType(type) {
        switch (type) {
            case 'success':
                return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
            case 'error':
                return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
            case 'info':
                return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
            default:
                return '';
        }
    }
}

// Crear una instancia global
const notifications = new NotificationSystem();

// Reemplazar la función showNotification existente
function showNotification(message, type = 'info', options = {}) {
    switch (type) {
        case 'success':
            return notifications.success(message, options);
        case 'error':
            return notifications.error(message, options);
        default:
            return notifications.info(message, options);
    }
}

// Función para obtener una cookie por nombre (para CSRF)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}