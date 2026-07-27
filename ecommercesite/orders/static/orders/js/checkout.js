/**
 * Script unificado para manejar el formulario de checkout, integración con Mercado Pago,
 * y visualización de datos de pago con mapas.
 * @module checkout
 */

/** @constant {Object} ERROR_MESSAGES - Mensajes de error centralizados */
const ERROR_MESSAGES = {
    REQUIRED_FIELD: 'Este campo es obligatorio',
    INVALID_EMAIL: 'Ingrese un correo electrónico válido',
    INVALID_PHONE: 'Ingrese un número válido (9 dígitos)',
    TERMS_REQUIRED: 'Debe aceptar los términos y condiciones',
    SYSTEM_ERROR: 'Error del sistema. Contacte al administrador.',
    INVALID_COORDINATES: 'Coordenadas no válidas',
};

/** @constant {Object} TAILWIND_CLASSES - Clases de Tailwind centralizadas */
const TAILWIND_CLASSES = {
    ERROR_BORDER: 'border-red-500',
    ERROR_TEXT: 'mt-1 text-xs text-red-500 field-error',
};

/** @constant {Object} elements - Caché de selectores DOM */
const elements = {
    stepIdentification: document.getElementById('step-identification'),
    stepShipping: document.getElementById('step-shipping'),
    backBtn: document.getElementById('back-to-identification'),
    identificationForm: document.getElementById('identification-form'),
    shippingForm: document.getElementById('shipping-form'),
    nextBtn: document.getElementById('continue-to-shipping'),
    payBtn: document.getElementById('payment-btn'),
    invoiceCheckbox: document.getElementById('id_invoice_requested'),
    documentFields: document.getElementById('document-fields'),
    emailField: document.getElementById('id_email'),
    firstNameField: document.getElementById('id_first_name'),
    lastNameField: document.getElementById('id_last_name'),
    phoneField: document.getElementById('id_phone'),
    termsCheckbox: document.getElementById('id_terms_accepted'),
    departmentField: document.getElementById('id_department'),
    provinceField: document.getElementById('id_province'),
    districtField: document.getElementById('id_district'),
    streetField: document.getElementById('id_street'),
    streetNumberField: document.getElementById('id_street_number'),
    recipientField: document.getElementById('id_recipient'),
    documentType: document.getElementById('id_document_type'),
    documentNumber: document.getElementById('id_document_number'),
    additionalInfo: document.getElementById('id_additional_info'),
    isDefault: document.getElementById('id_is_default'),
    latitude: document.getElementById('latitude'),
    longitude: document.getElementById('longitude'),
    saveAddress: document.getElementById('id_save_address'),
    apartment: document.getElementById('id_apartment'),
    reference: document.getElementById('id_reference'),
};

// Debug: Verificar elementos DOM al cargar
console.log('Debug - Verificación de elementos DOM:');
console.log('documentType element:', elements.documentType);
console.log('documentNumber element:', elements.documentNumber);
console.log('documentType exists:', !!elements.documentType);
console.log('documentNumber exists:', !!elements.documentNumber);

/** @type {Object} Estado de Mercado Pago */
let mp;
let mpInitialized = false;

/** @type {Object} Configuración de variables de entorno */
const envConfig = {
    required: {
        MERCADOPAGO_PUBLIC_KEY: typeof MERCADOPAGO_PUBLIC_KEY !== 'undefined' ? MERCADOPAGO_PUBLIC_KEY : null,
    },
    optional: {
        GOOGLE_MAPS_API_KEY: typeof GOOGLE_MAPS_API_KEY !== 'undefined' ? GOOGLE_MAPS_API_KEY : null,
    },
    validateRequired() {
        const missingVars = Object.entries(this.required)
            .filter(([, value]) => !value)
            .map(([key]) => key);
        missingVars.forEach(key => console.error(`Error: La variable de entorno ${key} no está definida`));
        return { isValid: missingVars.length === 0, missingVars };
    },
    validateOptional() {
        const missingVars = Object.entries(this.optional)
            .filter(([, value]) => !value)
            .map(([key]) => key);
        missingVars.forEach(key => console.warn(`Advertencia: La variable de entorno opcional ${key} no está definida`));
        return { missingVars };
    },
    validateAll() {
        const required = this.validateRequired();
        const optional = this.validateOptional();
        return { isValid: required.isValid, missingRequired: required.missingVars, missingOptional: optional.missingVars };
    },
};

/** @type {Object} Validación de entorno */
const envValidation = envConfig.validateAll();

/** @type {Object} Almacena los datos del pedido */
let orderData = {
    identification: {},
    shipping: {},
    payment: {},
};

document.addEventListener('DOMContentLoaded', () => {
    // Configurar entorno de producción
    const isProduction = document.body.dataset.production === 'true';
    if (isProduction) {
        ['log', 'debug', 'info'].forEach(method => {
            console[method] = () => {};
        });
        window.addEventListener('error', event => {
            if (typeof Sentry !== 'undefined') {
                Sentry.captureException(event.error);
            }
            showNotification('Error inesperado. Intente nuevamente.', 'error');
            event.preventDefault();
        });
    }

    // Inicializar Mercado Pago
    if (envConfig.required.MERCADOPAGO_PUBLIC_KEY) {
        try {
            mp = new MercadoPago(envConfig.required.MERCADOPAGO_PUBLIC_KEY, { locale: 'es-PE' });
            mpInitialized = true;
            console.log('SDK de Mercado Pago inicializado correctamente');
        } catch (error) {
            handleError(error, 'MercadoPago Initialization');
        }
    }

    // Cargar datos guardados
    loadOrderData();

    // Validaciones en tiempo real
    setupRealTimeValidation();

    // Los campos de documento ahora siempre están visibles porque son requeridos por Mercado Pago
    // No es necesario mostrar/ocultar según el checkbox de factura

    // Botón de volver
    if (elements.backBtn) {
        elements.backBtn.addEventListener('click', () => {
            transitionSteps(elements.stepShipping, elements.stepIdentification);
        });
    }

    // Validación y envío de identificación
    if (elements.identificationForm && elements.nextBtn) {
        elements.identificationForm.addEventListener('submit', e => {
            e.preventDefault();
            validateAndSubmitIdentification();
        });
    }

    // Validación y envío de envío
    if (elements.shippingForm && elements.payBtn) {
        elements.shippingForm.addEventListener('submit', e => {
            e.preventDefault();
            validateAndSubmitShipping();
        });
        elements.payBtn.addEventListener('click', e => {
            e.preventDefault();
            elements.shippingForm.dispatchEvent(new Event('submit'));
        });
    }

    // Configurar evento HTMX para procesar respuestas del backend
    document.body.addEventListener('htmx:afterRequest', event => {
        if (event.detail?.xhr?.responseText) {
            try {
                const response = JSON.parse(event.detail.xhr.responseText);
                orderData.payment = {
                    payment_id: response.payment_id || response.id || '',
                    payment_status: response.payment_status || response.status || '',
                    payment_preference_id: response.payment_preference_id || response.preference_id || '',
                    external_reference: response.external_reference || '',
                    request_token: response.request_token || '',
                    latitude: response.latitude || '',
                    longitude: response.longitude || '',
                };
                mostrarDatosPagoYMapa(orderData.payment);
            } catch (e) {
                console.warn('Respuesta no JSON en HTMX:', e);
            }
        }
    });
});

/**
 * Maneja errores y los registra en Sentry si está disponible.
 * @param {Error} error - El error a manejar.
 * @param {string} context - Contexto del error.
 */
function handleError(error, context) {
    console.error(`[${context}] Error:`, error);
    if (typeof Sentry !== 'undefined') {
        Sentry.captureException(error, { extra: { context } });
    }
    showNotification(`Error: ${error.message || ERROR_MESSAGES.SYSTEM_ERROR}`, 'error');
}

/**
 * Sanitiza una entrada para prevenir XSS.
 * @param {string} input - Entrada a sanitizar.
 * @returns {string} Entrada sanitizada.
 */
function sanitizeInput(input) {
    return input ? input.replace(/[<>]/g, '') : '';
}

/**
 * Cifra datos para sessionStorage.
 * @param {string} data - Dato a cifrar.
 * @returns {string} Dato cifrado.
 */
function encryptData(data) {
    return btoa(data);
}

/**
 * Descifra datos de sessionStorage.
 * @param {string} data - Dato cifrado.
 * @returns {string} Dato descifrado.
 */
function decryptData(data) {
    try {
        return atob(data);
    } catch {
        return '';
    }
}

/**
 * Valida un correo electrónico.
 * @param {string} email - Correo a validar.
 * @returns {boolean} Verdadero si es válido.
 */
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Valida un número de teléfono.
 * @param {string} phone - Teléfono a validar.
 * @returns {boolean} Verdadero si es válido.
 */
function isValidPhone(phone) {
    return /^[0-9]{9}$/.test(phone.replace(/\s+/g, ''));
}

/**
 * Muestra un error en un campo del formulario.
 * @param {HTMLElement} field - Campo del formulario.
 * @param {string} message - Mensaje de error.
 */
function showFieldError(field, message) {
    if (!field) return;
    field.setAttribute('aria-invalid', 'true');
    field.classList.add(TAILWIND_CLASSES.ERROR_BORDER);
    const parent = field.parentNode;
    let errorElement = parent.querySelector('.field-error');
    if (!errorElement) {
        errorElement = document.createElement('p');
        errorElement.id = `${field.id}-error`;
        errorElement.className = TAILWIND_CLASSES.ERROR_TEXT;
        errorElement.setAttribute('role', 'alert');
        parent.appendChild(errorElement);
        field.setAttribute('aria-describedby', errorElement.id);
    }
    errorElement.textContent = message;
}

/**
 * Elimina un error de un campo del formulario.
 * @param {HTMLElement} field - Campo del formulario.
 */
function removeFieldError(field) {
    if (!field) return;
    field.removeAttribute('aria-invalid');
    field.removeAttribute('aria-describedby');
    field.classList.remove(TAILWIND_CLASSES.ERROR_BORDER);
    const parent = field.parentNode;
    const errorElement = parent.querySelector('.field-error');
    if (errorElement) errorElement.remove();
}

/**
 * Muestra una notificación al usuario.
 * @param {string} message - Mensaje a mostrar.
 * @param {string} [type=info] - Tipo de notificación (success, error, warning, info).
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
    notification.setAttribute('role', 'alert');

    const typeStyles = {
        success: 'bg-green-100 border-l-4 border-green-500 text-green-700',
        error: 'bg-red-100 border-l-4 border-red-500 text-red-700',
        warning: 'bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700',
        info: 'bg-blue-100 border-l-4 border-blue-500 text-blue-700',
    };
    notification.classList.add(...typeStyles[type].split(' '));
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
 * Obtiene un valor de cookie.
 * @param {string} name - Nombre de la cookie.
 * @returns {string|null} Valor de la cookie o null.
 */
function getCookie(name) {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith(`${name}=`))
        ?.split('=')[1];
    return cookieValue ? decodeURIComponent(cookieValue) : null;
}

/**
 * Obtiene el token CSRF priorizando el meta tag (compatible con CSRF_USE_SESSIONS).
 */
function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        const token = metaTag.getAttribute('content');
        if (token) return token;
    }
    return getCookie('csrftoken');
}

/**
 * Implementa debouncing para eventos.
 * @param {Function} func - Función a debouncer.
 * @param {number} wait - Tiempo de espera en ms.
 * @returns {Function} Función debounced.
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

/**
 * Muestra un overlay de carga.
 */
function showLoadingOverlay() {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'flex fixed inset-0 z-50 justify-center items-center bg-gray-500 bg-opacity-50';
        overlay.innerHTML = `
            <div class="inline-block w-8 h-8 rounded-full border-4 animate-spin spinner-border" role="status">
                <span class="sr-only">Cargando...</span>
            </div>
        `;
        document.body.appendChild(overlay);
    }
}

/**
 * Oculta el overlay de carga.
 */
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.remove();
}

/**
 * Realiza una transición suave entre pasos.
 * @param {HTMLElement} fromStep - Paso a ocultar.
 * @param {HTMLElement} toStep - Paso a mostrar.
 */
function transitionSteps(fromStep, toStep) {
    if (fromStep && toStep) {
        fromStep.classList.add('opacity-0');
        setTimeout(() => {
            fromStep.classList.add('hidden');
            fromStep.classList.remove('opacity-0');
            toStep.classList.remove('hidden');
            toStep.classList.add('opacity-0');
            setTimeout(() => toStep.classList.remove('opacity-0'), 50);
        }, 300);
    }
}

/**
 * Configura validaciones en tiempo real.
 */
function setupRealTimeValidation() {
    const validations = [
        { field: elements.emailField, validator: isValidEmail, error: ERROR_MESSAGES.INVALID_EMAIL, required: true },
        { field: elements.phoneField, validator: isValidPhone, error: ERROR_MESSAGES.INVALID_PHONE, required: true },
        { field: elements.firstNameField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'nombre' },
        { field: elements.lastNameField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'apellidos' },
        { field: elements.departmentField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'departamento' },
        { field: elements.provinceField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'provincia' },
        { field: elements.districtField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'distrito' },
        { field: elements.streetField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'calle' },
        { field: elements.streetNumberField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'número' },
        { field: elements.recipientField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'destinatario', required: false },
        { field: elements.documentType, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'tipo de documento', required: true },
        { field: elements.documentNumber, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'número de documento', required: true },
    ];

    validations.forEach(({ field, validator, error, name, required }) => {
        if (!field) return;
        field.addEventListener('blur', debounce(() => {
            const value = field.value.trim();
            const isRequired = typeof required === 'function' ? required() : required;
            if (isRequired && !value) {
                showFieldError(field, name ? `El ${name} es obligatorio` : error);
            } else if (value && !validator(value)) {
                showFieldError(field, error);
            } else {
                removeFieldError(field);
            }
        }, 300));
    });
}

/**
 * Carga los datos del pedido desde sessionStorage.
 */
function loadOrderData() {
    // Recuperar datos de sessionStorage
    const userEmail = sessionStorage.getItem('userEmail');
    const userFirstName = sessionStorage.getItem('userFirstName');
    const userLastName = sessionStorage.getItem('userLastName');
    const userPhone = sessionStorage.getItem('userPhone');
    const userDocumentType = sessionStorage.getItem('userDocumentType');
    const userDocumentNumber = sessionStorage.getItem('userDocumentNumber');
    const userInvoiceRequested = sessionStorage.getItem('userInvoiceRequested');
    
    // Cargar datos en el objeto orderData
    orderData.identification = {
        email: userEmail ? decryptData(userEmail) : '',
        first_name: userFirstName ? decryptData(userFirstName) : '',
        last_name: userLastName ? decryptData(userLastName) : '',
        phone: userPhone ? decryptData(userPhone) : '',
        document_type: userDocumentType ? decryptData(userDocumentType) : '',
        document_number: userDocumentNumber ? decryptData(userDocumentNumber) : '',
        invoice_requested: userInvoiceRequested === 'true',
        terms_accepted: true
    };

    // Actualizar campos del formulario con los datos cargados
    if (elements.emailField) elements.emailField.value = orderData.identification.email;
    if (elements.firstNameField) elements.firstNameField.value = orderData.identification.first_name;
    if (elements.lastNameField) elements.lastNameField.value = orderData.identification.last_name;
    if (elements.phoneField) elements.phoneField.value = orderData.identification.phone;
    if (elements.documentType) elements.documentType.value = orderData.identification.document_type;
    if (elements.documentNumber) elements.documentNumber.value = orderData.identification.document_number;
    if (elements.invoiceCheckbox) elements.invoiceCheckbox.checked = orderData.identification.invoice_requested;
    
    // Verificar si hay datos de documento faltantes y mostrar mensaje si es necesario
    if ((elements.documentType && !elements.documentType.value) || 
        (elements.documentNumber && !elements.documentNumber.value)) {
        console.warn('Datos de documento incompletos. Se requieren para proceder al pago.');
    }
    
    // Registrar en consola para depuración
    console.log('Datos cargados:', orderData.identification);
}

/**
 * Valida y envía el formulario de identificación.
 */
function validateAndSubmitIdentification() {
    let isValid = true;
    const validations = [
        { field: elements.emailField, validator: isValidEmail, error: ERROR_MESSAGES.INVALID_EMAIL, required: true },
        { field: elements.firstNameField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'nombre' },
        { field: elements.lastNameField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'apellidos' },
        { field: elements.phoneField, validator: isValidPhone, error: ERROR_MESSAGES.INVALID_PHONE, required: true },
        { field: elements.documentType, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'tipo de documento', required: true },
        { field: elements.documentNumber, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'número de documento', required: true },
    ];

    validations.forEach(({ field, validator, error, name, required }) => {
        if (!field) return;
        const value = field.value.trim();
        if (required && !value) {
            showFieldError(field, name ? `El ${name} es obligatorio` : error);
            isValid = false;
        } else if (value && !validator(value)) {
            showFieldError(field, error);
            isValid = false;
        } else {
            removeFieldError(field);
        }
    });



    if (!elements.termsCheckbox.checked) {
        const termsContainer = elements.termsCheckbox.closest('div');
        termsContainer.classList.add('p-2', 'border', 'border-red-500', 'rounded');
        showNotification(ERROR_MESSAGES.TERMS_REQUIRED, 'error');
        isValid = false;
    } else {
        const termsContainer = elements.termsCheckbox.closest('div');
        termsContainer.classList.remove('p-2', 'border', 'border-red-500', 'rounded');
    }



    if (!isValid) {
        const firstErrorField = document.querySelector('.border-red-500');
        if (firstErrorField) {
            firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstErrorField.focus({ preventScroll: true });
        }
        return;
    }

    showLoadingOverlay();
    
    // Debug: Verificar valores de los campos de documento
    console.log('Debug - elements.documentType:', elements.documentType);
    console.log('Debug - elements.documentNumber:', elements.documentNumber);
    console.log('Debug - documentType value:', elements.documentType?.value);
    console.log('Debug - documentNumber value:', elements.documentNumber?.value);
    
    orderData.identification = {
        email: sanitizeInput(elements.emailField.value),
        first_name: sanitizeInput(elements.firstNameField.value),
        last_name: sanitizeInput(elements.lastNameField.value),
        phone: sanitizeInput(elements.phoneField.value),
        invoice_requested: elements.invoiceCheckbox.checked,
        document_type: sanitizeInput(elements.documentType?.value || ''),
        document_number: sanitizeInput(elements.documentNumber?.value || ''),
        terms_accepted: elements.termsCheckbox.checked,
    };
    
    console.log('Debug - orderData.identification:', orderData.identification);

    fetch('/orders/save-identification/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(orderData.identification),
    })
        .then(response => {
            hideLoadingOverlay();
            if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Guardar todos los datos en sessionStorage, asegurando que los datos del documento se guarden correctamente
                // Guardar todos los datos en sessionStorage
                sessionStorage.setItem('userEmail', encryptData(orderData.identification.email));
                sessionStorage.setItem('userFirstName', encryptData(orderData.identification.first_name));
                sessionStorage.setItem('userLastName', encryptData(orderData.identification.last_name));
                sessionStorage.setItem('userPhone', encryptData(orderData.identification.phone));
                
                // Siempre guardar los datos del documento, son obligatorios para Mercado Pago
                sessionStorage.setItem('userDocumentType', encryptData(orderData.identification.document_type));
                sessionStorage.setItem('userDocumentNumber', encryptData(orderData.identification.document_number));
                sessionStorage.setItem('userInvoiceRequested', orderData.identification.invoice_requested);
                
                // Verificar que se guardaron correctamente
                console.log('Datos guardados en sessionStorage:', {
                    document_type: orderData.identification.document_type,
                    document_number: orderData.identification.document_number
                });
                transitionSteps(elements.stepIdentification, elements.stepShipping);
                showNotification('Datos de identificación guardados.', 'success');
            } else {
                throw new Error(data.errors ? Object.values(data.errors).join(', ') : data.error || 'Error desconocido');
            }
        })
        .catch(error => {
            hideLoadingOverlay();
            handleError(error, 'Identification Submission');
        });
}

/**
 * Valida y envía el formulario de envío.
 */
function validateAndSubmitShipping() {
    // Verificar primero si los datos de identificación están completos
    // Recuperar los datos más recientes del sessionStorage
    const userEmail = sessionStorage.getItem('userEmail');
    const userFirstName = sessionStorage.getItem('userFirstName');
    const userLastName = sessionStorage.getItem('userLastName');
    const userPhone = sessionStorage.getItem('userPhone');
    const userDocumentType = sessionStorage.getItem('userDocumentType');
    const userDocumentNumber = sessionStorage.getItem('userDocumentNumber');
    
    // Verificar si los datos básicos de identificación están completos
    if (!userEmail || !userFirstName || !userLastName || !userPhone) {
        showNotification('Por favor complete el paso de identificación antes de continuar.', 'error');
        transitionSteps(elements.stepShipping, elements.stepIdentification);
        return;
    }
    
    // Verificar si los datos de documento están completos
    const documentType = userDocumentType ? decryptData(userDocumentType) : '';
    const documentNumber = userDocumentNumber ? decryptData(userDocumentNumber) : '';
    
    if (!documentType || !documentNumber) {
        showNotification('Por favor complete los datos de documento en el paso de identificación antes de continuar.', 'error');
        transitionSteps(elements.stepShipping, elements.stepIdentification);
        return;
    }
    
    // Actualizar orderData con los valores más recientes
    orderData.identification = {
        email: userEmail ? decryptData(userEmail) : '',
        first_name: userFirstName ? decryptData(userFirstName) : '',
        last_name: userLastName ? decryptData(userLastName) : '',
        phone: userPhone ? decryptData(userPhone) : '',
        document_type: documentType,
        document_number: documentNumber,
        invoice_requested: sessionStorage.getItem('userInvoiceRequested') === 'true',
        terms_accepted: true
    };
    
    console.log('Datos de identificación recuperados:', orderData.identification);

    let isValid = true;
    const validations = [
        { field: elements.departmentField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'departamento' },
        { field: elements.provinceField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'provincia' },
        { field: elements.districtField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'distrito' },
        { field: elements.streetField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'calle' },
        { field: elements.streetNumberField, validator: val => !!val, error: ERROR_MESSAGES.REQUIRED_FIELD, name: 'número' },
    ];

    validations.forEach(({ field, validator, error, name }) => {
        if (!field) return;
        const value = field.value.trim();
        if (!value) {
            showFieldError(field, name ? `El ${name} es obligatorio` : error);
            isValid = false;
        } else if (!validator(value)) {
            showFieldError(field, error);
            isValid = false;
        } else {
            removeFieldError(field);
        }
    });

    if (elements.recipientField) removeFieldError(elements.recipientField); // Opcional

    if (!isValid) {
        const firstErrorField = document.querySelector('.border-red-500');
        if (firstErrorField) {
            firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstErrorField.focus({ preventScroll: true });
        }
        return;
    }

    showLoadingOverlay();
    orderData.shipping = {
        department: sanitizeInput(elements.departmentField.value),
        province: sanitizeInput(elements.provinceField.value),
        district: sanitizeInput(elements.districtField.value),
        street: sanitizeInput(elements.streetField.value),
        street_number: sanitizeInput(elements.streetNumberField.value),
        recipient: sanitizeInput(elements.recipientField?.value || ''),
        additional_info: sanitizeInput(elements.additionalInfo?.value || ''),
        is_default: elements.isDefault?.checked || false,
        latitude: elements.latitude?.value || null,
        longitude: elements.longitude?.value || null,
        save_address: elements.saveAddress?.checked || false,
        apartment: sanitizeInput(elements.apartment?.value || ''),
        reference: sanitizeInput(elements.reference?.value || ''),
    };

    // Combinar identificación y envío para guardar en la sesión
    const sessionData = {
        identification_data: orderData.identification,
        shipping_data: orderData.shipping,
    };

    fetch('/orders/save-session-data/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(sessionData),
    })
        .then(response => {
            if (!response.ok) {
                // Intentar leer el mensaje de error del servidor
                return response.json().then(data => {
                    throw new Error(data.error || `Error del servidor (${response.status})`);
                }).catch(err => {
                    if (err instanceof SyntaxError) {
                        throw new Error(`Error del servidor (${response.status})`);
                    }
                    throw err;
                });
            }
            return response.json();
        })
        .then(data => {
            if (!data.success) {
                throw new Error(data.errors ? Object.values(data.errors).join(', ') : data.error || 'Error desconocido');
            }

            // Proceder al pago
            if (!mpInitialized) {
                throw new Error('Mercado Pago no inicializado');
            }

            elements.payBtn.disabled = true;
            elements.payBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';

            return fetch('/orders/create-payment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(orderData.identification),
            });
        })
        .then(response => {
            if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            if (data.init_point) {
                window.location.href = data.init_point;
            } else if (data.id && mpInitialized) {
                mp.checkout({
                    preference: { id: data.id },
                    autoOpen: true,
                });
            } else {
                throw new Error(data.error || 'Respuesta inválida del servidor');
            }
        })
        .catch(error => {
            elements.payBtn.disabled = false;
            elements.payBtn.innerHTML = 'Pagar con Mercado Pago';
            handleError(error, 'Shipping and Payment Submission');
        })
        .finally(() => {
            hideLoadingOverlay();
        });
}

/**
 * Muestra los datos de pago y un mapa si hay coordenadas.
 * @param {Object} datos - Datos del pago.
 */
function mostrarDatosPagoYMapa(datos) {
    const contenedor = document.getElementById('payment-result-container') || document.createElement('div');
    if (!contenedor.id) {
        contenedor.id = 'payment-result-container';
        contenedor.className = 'p-4 my-4 bg-gray-100 rounded shadow';
        const paymentBtn = elements.payBtn;
        if (paymentBtn && paymentBtn.parentNode) {
            paymentBtn.parentNode.insertBefore(contenedor, paymentBtn.nextSibling);
        } else {
            document.body.appendChild(contenedor);
        }
    }

    contenedor.innerHTML = '';
    const lista = document.createElement('ul');
    lista.className = 'pl-5 mb-2 list-disc';
    const addItem = (label, value) => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${sanitizeInput(label)}:</strong> ${value ? sanitizeInput(value) : '<span class="text-gray-400">No disponible</span>'}`;
        lista.appendChild(li);
    };

    addItem('ID de pago', datos.payment_id);
    addItem('Estado', datos.payment_status);
    addItem('ID de preferencia', datos.payment_preference_id);
    addItem('Referencia externa', datos.external_reference);
    addItem('Token de solicitud', datos.request_token);
    addItem('Latitud', datos.latitude);
    addItem('Longitud', datos.longitude);

    contenedor.appendChild(lista);

    const latitude = parseFloat(datos.latitude);
    const longitude = parseFloat(datos.longitude);
    if (!isNaN(latitude) && !isNaN(longitude) && Math.abs(latitude) <= 90 && Math.abs(longitude) <= 180) {
        if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
            const mapaDiv = document.createElement('div');
            mapaDiv.id = 'payment-map-preview';
            mapaDiv.style.width = '100%';
            mapaDiv.style.height = '300px';
            mapaDiv.className = 'mb-2 rounded border';
            mapaDiv.setAttribute('aria-label', 'Mapa con ubicación del pago');
            contenedor.appendChild(mapaDiv);

            const latLng = { lat: latitude, lng: longitude };
            const map = new google.maps.Map(mapaDiv, {
                center: latLng,
                zoom: 15,
            });
            new google.maps.Marker({ position: latLng, map, title: 'Ubicación del pago' });
        } else if (envConfig.optional.GOOGLE_MAPS_API_KEY) {
            loadGoogleMapsApi(latitude, longitude, contenedor);
        } else {
            const link = document.createElement('a');
            link.href = `https://maps.google.com/?q=${latitude},${longitude}`;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = 'Ver ubicación en Google Maps';
            link.className = 'text-blue-600 underline';
            link.setAttribute('aria-label', 'Abrir ubicación en Google Maps');
            contenedor.appendChild(link);
        }
    } else if (datos.latitude || datos.longitude) {
        showNotification(ERROR_MESSAGES.INVALID_COORDINATES, 'warning');
    }
}

/**
 * Carga la API de Google Maps asíncronamente.
 * @param {number} latitude - Latitud.
 * @param {number} longitude - Longitud.
 * @param {HTMLElement} contenedor - Contenedor del mapa.
 */
function loadGoogleMapsApi(latitude, longitude, contenedor) {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${envConfig.optional.GOOGLE_MAPS_API_KEY}&callback=initMap`;
    script.async = true;
    script.defer = true;
    window.initMap = () => {
        const mapaDiv = document.createElement('div');
        mapaDiv.id = 'payment-map-preview';
        mapaDiv.style.width = '100%';
        mapaDiv.style.height = '300px';
        mapaDiv.className = 'mb-2 rounded border';
        contenedor.appendChild(mapaDiv);

        const latLng = { lat: latitude, lng: longitude };
        const map = new google.maps.Map(mapaDiv, {
            center: latLng,
            zoom: 15,
        });
        new google.maps.Marker({ position: latLng, map });
    };
    document.head.appendChild(script);
}

/**
 * Recolecta y devuelve todos los datos del pedido.
 * @returns {Object} Datos completos del pedido.
 */
function collectOrderData() {
    return { ...orderData };
}