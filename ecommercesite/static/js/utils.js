/**
 * Utilidades generales para el sitio de ecommerce
 */

// Función para mostrar mensajes de error
function showError(message, elementId = null) {
    if (elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.classList.remove('hidden');
        }
    } else {
        alert(message);
    }
}

// Función para ocultar mensajes de error
function hideError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = '';
        element.classList.add('hidden');
    }
}

// Función para validar un correo electrónico
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Función para validar un número de teléfono peruano
function isValidPhone(phone) {
    // Acepta formatos: 999999999, +51999999999, 51999999999
    const re = /^(\+?51)?9\d{8}$/;
    return re.test(phone.replace(/\s/g, ''));
}

// Función para enviar datos al servidor mediante fetch
async function sendDataToServer(url, data, method = 'POST') {
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error en la solicitud');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error al enviar datos:', error);
        throw error;
    }
}

// Función para validar formularios genéricos
function validateForm(formId, validationRules) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    
    // Recorrer todas las reglas de validación
    for (const fieldId in validationRules) {
        const field = document.getElementById(fieldId);
        const errorId = `${fieldId}-error`;
        const rules = validationRules[fieldId];
        
        if (!field) continue;
        
        // Limpiar error previo
        hideError(errorId);
        
        // Validar campo requerido
        if (rules.required && !field.value.trim()) {
            showError(rules.requiredMessage || 'Este campo es obligatorio', errorId);
            isValid = false;
            continue;
        }
        
        // Validar con función personalizada si existe
        if (rules.validator && typeof rules.validator === 'function') {
            if (!rules.validator(field.value)) {
                showError(rules.validatorMessage || 'Valor inválido', errorId);
                isValid = false;
            }
        }
    }
    
    return isValid;
}

// Exportar funciones para uso global
window.showError = showError;
window.hideError = hideError;
window.isValidEmail = isValidEmail;
window.isValidPhone = isValidPhone;
window.sendDataToServer = sendDataToServer;
window.validateForm = validateForm;