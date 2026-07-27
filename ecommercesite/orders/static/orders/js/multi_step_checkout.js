// ecommercesite\orders\static\orders\js\multi_step_checkout.js
document.addEventListener('DOMContentLoaded', function () {
    const checkoutSteps = document.querySelectorAll('.checkout-step');
    const progressBar = document.querySelector('.checkout-progress-bar');
    const progressSteps = document.querySelectorAll('.progress-step');
    const progressPercentage = document.getElementById('progress-percentage');
    const currentStepText = document.querySelector('.current-step-text');
    const nextButtons = document.querySelectorAll('.btn-next-step');
    const prevButtons = document.querySelectorAll('.btn-prev-step');
    const paymentBtn = document.getElementById('payment-btn');

    let currentStep = 0;

    // Verificar si las cookies están habilitadas con múltiples métodos
    function areCookiesEnabled() {
        if (navigator && typeof navigator.cookieEnabled !== 'undefined') {
            if (navigator.cookieEnabled === false) {
                console.warn('Cookies deshabilitadas según navigator.cookieEnabled');
                return false;
            }
        }

        try {
            const testCookieName = 'testcookie_' + Math.random().toString(36).substring(2, 10);
            const testCookieValue = 'test_value_' + Date.now();
            const expires = new Date(Date.now() + 1000).toUTCString();

            document.cookie = `${testCookieName}=${testCookieValue}; expires=${expires}; path=/; SameSite=Lax`;

            const cookieExists = document.cookie.indexOf(testCookieName) !== -1;

            document.cookie = `${testCookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;

            if (!cookieExists) {
                console.warn('No se pudo establecer la cookie de prueba');
                return false;
            }

            return true;
        } catch (e) {
            console.error('Error al verificar cookies:', e);
            return false;
        }
    }

    function checkCookiesOnLoad() {
        if (!areCookiesEnabled()) {
            console.error('Las cookies están deshabilitadas en este navegador');
            showGlobalError('Las cookies están deshabilitadas en tu navegador. Para usar esta página correctamente, debes habilitar las cookies en la configuración de tu navegador.');
            showCookieInstructions();
            return false;
        }
        return true;
    }

    function verificarCookiesAntesDeOperacion(operacion) {
        if (!areCookiesEnabled()) {
            console.error('Error: No hay cookies disponibles');
            showGlobalError('Las cookies están deshabilitadas en tu navegador. Para continuar con el proceso de compra, por favor habilita las cookies.');
            showCookieInstructions();
            return false;
        }
        return true;
    }

    function updatePaymentSummary() {
        // Datos personales
        const firstName = document.getElementById('id_first_name')?.value || '';
        const lastName = document.getElementById('id_last_name')?.value || '';
        const email = document.getElementById('id_email')?.value || '';
        const phone = document.getElementById('id_phone')?.value || '';
        // Dirección de envío
        const street = document.getElementById('id_street')?.value || '';
        const streetNumber = document.getElementById('id_street_number')?.value || '';
        const district = document.getElementById('id_district')?.value || '';
        const province = document.getElementById('id_province')?.value || '';
        const department = document.getElementById('id_department')?.value || '';
        // Mostrar en resumen
        document.getElementById('summary-customer-name').textContent = (firstName || lastName) ? `${firstName} ${lastName}`.trim() : '-';
        document.getElementById('summary-customer-email').textContent = email || '-';
        document.getElementById('summary-customer-phone').textContent = phone || '-';
        let address = [street, streetNumber, district, province, department].filter(Boolean).join(', ');
        document.getElementById('summary-shipping-address').textContent = address || '-';
    }

    function showStep(stepIndex) {
        checkoutSteps.forEach((step, index) => {
            step.classList.toggle('active', index === stepIndex);
            step.classList.toggle('hidden', index !== stepIndex);
        });
        currentStep = stepIndex;
        // Actualizar resumen solo en el paso de pago
        if (checkoutSteps[stepIndex].id === 'step-payment') {
            updatePaymentSummary();
        }
    }

    function updateProgressBar() {
        const totalSteps = checkoutSteps.length; // 3 pasos
        let displayPercentage = Math.round((currentStep / (totalSteps - 1)) * 100);
        displayPercentage = Math.max(0, Math.min(displayPercentage, 100));

        // Actualizar barra de progreso y porcentaje
        if (progressBar) {
            progressBar.style.width = `${displayPercentage}%`;
        }
        if (progressPercentage) {
            progressPercentage.textContent = `${displayPercentage}%`;
            // Alinear el porcentaje con los iconos de los pasos
            if (currentStep === 0) {
                progressPercentage.style.left = '0%';
                progressPercentage.style.transform = 'translateY(-50%) translateX(0)';
            } else if (currentStep === 1) {
                progressPercentage.style.left = '50%';
                progressPercentage.style.transform = 'translateY(-50%) translateX(-50%)';
            } else if (currentStep === 2) {
                progressPercentage.style.left = '100%';
                progressPercentage.style.transform = 'translateY(-50%) translateX(-100%)';
            } else {
                progressPercentage.style.left = `${displayPercentage}%`;
                progressPercentage.style.transform = 'translateY(-50%)';
            }
        }
        progressPercentage.style.left = `${displayPercentage}%`;
    }

    function showGlobalError(message) {
        const checkoutContainer = document.querySelector('.container');
        if (!checkoutContainer) return;

        const existingErrors = document.querySelectorAll('.global-error');
        existingErrors.forEach(el => el.remove());

        const errorElement = document.createElement('div');
        errorElement.className = 'px-4 py-3 mb-4 text-red-700 bg-red-100 rounded border border-red-400 global-error';
        errorElement.setAttribute('role', 'alert');
        errorElement.innerHTML = `<p class="font-bold">Error</p><p>${message}</p>`;

        checkoutContainer.insertBefore(errorElement, checkoutContainer.firstChild);
    }

    function showCookieInstructions() {
        const checkoutContainer = document.querySelector('.container');
        if (!checkoutContainer) return;

        const instructionsElement = document.createElement('div');
        instructionsElement.className = 'p-4 mt-4 bg-blue-50 rounded-md border border-blue-200 cookie-instructions';

        instructionsElement.innerHTML = `
            <h3 class="mb-2 text-lg font-bold">Cómo habilitar cookies:</h3>
            <div class="space-y-3">
                <div>
                    <p class="font-semibold">Chrome:</p>
                    <ol class="pl-5 list-decimal">
                        <li>Haz clic en los tres puntos en la esquina superior derecha</li>
                        <li>Selecciona "Configuración"</li>
                        <li>Busca "Privacidad y seguridad"</li>
                        <li>Haz clic en "Cookies y otros datos de sitios"</li>
                        <li>Asegúrate de que "Permitir que los sitios guarden y lean datos de cookies" esté activado</li>
                    </ol>
                </div>
                <div>
                    <p class="font-semibold">Firefox:</p>
                    <ol class="pl-5 list-decimal">
                        <li>Haz clic en las tres líneas en la esquina superior derecha</li>
                        <li>Selecciona "Opciones" o "Preferencias"</li>
                        <li>Ve a "Privacidad y seguridad"</li>
                        <li>En "Cookies y datos del sitio", selecciona "Aceptar cookies y datos del sitio"</li>
                    </ol>
                </div>
                <div>
                    <p class="font-semibold">Safari:</p>
                    <ol class="pl-5 list-decimal">
                        <li>Haz clic en "Safari" en la barra de menú</li>
                        <li>Selecciona "Preferencias"</li>
                        <li>Ve a la pestaña "Privacidad"</li>
                        <li>Desactiva "Bloquear todas las cookies"</li>
                    </ol>
                </div>
                <div>
                    <p class="font-semibold">Edge:</p>
                    <ol class="pl-5 list-decimal">
                        <li>Haz clic en los tres puntos en la esquina superior derecha</li>
                        <li>Selecciona "Configuración"</li>
                        <li>Ve a "Cookies y permisos del sitio"</li>
                        <li>Asegúrate de que no estén bloqueadas las cookies</li>
                    </ol>
                </div>
                <p class="mt-2">Después de habilitar las cookies, <a href="javascript:location.reload()" class="text-blue-600 underline">recarga la página</a>.</p>
            </div>`;

        const globalError = checkoutContainer.querySelector('.global-error');
        if (globalError) {
            globalError.after(instructionsElement);
        } else {
            checkoutContainer.insertBefore(instructionsElement, checkoutContainer.firstChild);
        }
    }

    function getCookie(name) {
        if (!document.cookie || document.cookie === '') {
            if (name === 'csrftoken') {
                console.log('Información: No hay cookies disponibles, intentando obtener token CSRF de otras fuentes');
            }
            return null;
        }

        try {
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith(`${name}=`))
                ?.split('=')[1];

            if (cookieValue) {
                return decodeURIComponent(cookieValue);
            }
        } catch (e) {
            console.warn('Error al procesar cookie con método moderno:', e);
        }

        try {
            const cookieRegex = new RegExp(`(?:^|; )${name.replace(/([.$?*|{}()[\]\\])/g, '\\$1')}=([^;]*)`);
            const matches = document.cookie.match(cookieRegex);
            if (matches) {
                return decodeURIComponent(matches[1]);
            }
        } catch (e) {
            console.warn('Error al procesar cookie con regex:', e);
        }

        try {
            const cookies = document.cookie.split('; ');
            for (let i = 0; i < cookies.length; i++) {
                const parts = cookies[i].split('=');
                if (parts[0] === name) {
                    return decodeURIComponent(parts[1] || '');
                }
            }
        } catch (e) {
            console.warn('Error al procesar cookie con método manual:', e);
        }

        if (name === 'csrftoken') {
            console.error('Error: No se pudo obtener el token CSRF');
            showGlobalError('Error de autenticación. Por favor, recarga la página para continuar. Si el problema persiste, borra las cookies del navegador e inténtalo de nuevo.');
        }

        return null;
    }

    function sanitizeInput(input) {
        if (!input) return '';
        return input.trim();
    }

    function isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function isValidPhone(phone) {
        const re = /^(\+?51)?9\d{8}$/;
        return re.test(phone.replace(/\s/g, ''));
    }

    function validateIdentificationForm() {
        const fields = [
            { id: 'id_first_name', label: 'Nombre' },
            { id: 'id_last_name', label: 'Apellidos' },
            { id: 'id_email', label: 'Correo electrónico' },
            { id: 'id_phone', label: 'Teléfono' },
            { id: 'id_document_number', label: 'Número de Documento' }
        ];
        let valid = true;

        fields.forEach(field => {
            const input = document.getElementById(field.id);
            if (!input.value.trim()) {
                showFieldError(input, `${field.label} es obligatorio`);
                valid = false;
            } else {
                removeFieldError(input);
            }
        });

        const email = document.getElementById('id_email');
        if (email && !isValidEmail(email.value)) {
            showFieldError(email, 'Correo electrónico no válido');
            valid = false;
        }

        const phone = document.getElementById('id_phone');
        if (phone && phone.value && !isValidPhone(phone.value)) {
            showFieldError(phone, 'El teléfono debe tener 9 dígitos');
            valid = false;
        }

        return valid;
    }

    function validateShippingForm() {
        const fields = [
            { id: 'id_department', label: 'Departamento' },
            { id: 'id_province', label: 'Provincia' },
            { id: 'id_district', label: 'Distrito' },
            { id: 'id_street', label: 'Calle' },
            { id: 'id_street_number', label: 'Número' }
        ];

        let valid = true;
        fields.forEach(field => {
            const input = document.getElementById(field.id);
            if (!input.value) {
                showFieldError(input, `${field.label} es obligatorio`);
                valid = false;
            } else {
                removeFieldError(input);
            }
        });
        return valid;
    }

    function saveDataToServerSession() {
        if (!verificarCookiesAntesDeOperacion('guardar datos')) {
            return Promise.reject('Error: Las cookies están deshabilitadas. No se pueden guardar los datos.');
        }

        let csrfToken = getCookie('csrftoken');

        if (!csrfToken) {
            const metaTag = document.querySelector('meta[name="csrf-token"]');
            if (metaTag) {
                csrfToken = metaTag.getAttribute('content');
                console.log('Token CSRF obtenido desde meta tag');
            }

            if (!csrfToken) {
                const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
                if (csrfInput) {
                    csrfToken = csrfInput.value;
                    console.log('Token CSRF obtenido desde input hidden');
                }
            }
        }

        if (!csrfToken) {
            console.error('Error: No se pudo obtener el token CSRF por ningún método');
            showGlobalError('Error de autenticación. Por favor, intenta las siguientes soluciones: 1) Recarga la página, 2) Borra las cookies del navegador, 3) Usa otro navegador, o 4) Desactiva extensiones que puedan estar bloqueando cookies.');
            return Promise.reject('Error de autenticación. No se pudo obtener el token CSRF.');
        }

        const identification_data = {
            email: sanitizeInput(document.getElementById('id_email')?.value),
            first_name: sanitizeInput(document.getElementById('id_first_name')?.value),
            last_name: sanitizeInput(document.getElementById('id_last_name')?.value),
            phone: sanitizeInput(document.getElementById('id_phone')?.value),
            document_type: sanitizeInput(document.getElementById('id_document_type')?.value),
            document_number: sanitizeInput(document.getElementById('id_document_number')?.value)
        };

        const shipping_data = {
            department: sanitizeInput(document.getElementById('id_department')?.value),
            province: sanitizeInput(document.getElementById('id_province')?.value),
            district: sanitizeInput(document.getElementById('id_district')?.value),
            street: sanitizeInput(document.getElementById('id_street')?.value),
            street_number: sanitizeInput(document.getElementById('id_street_number')?.value),
            additional_info: sanitizeInput(document.getElementById('id_additional_info')?.value),
            latitude: document.getElementById('latitude')?.value || null,
            longitude: document.getElementById('longitude')?.value || null
        };

        console.log('Enviando datos con token CSRF:', csrfToken.substring(0, 5) + '...');

        return fetch('/orders/save-session-data/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin',
            body: JSON.stringify({ identification_data, shipping_data })
        })
        .then(res => {
            if (!res.ok) {
                if (res.status === 403) {
                    console.error('Error CSRF: Token inválido o expirado');
                    showGlobalError('Error de autenticación. Por favor, recarga la página para continuar. Si el problema persiste, borra las cookies del navegador e inténtalo de nuevo.');
                    throw new Error('Error de autenticación. Token CSRF inválido o expirado.');
                }
                throw new Error('Error en la solicitud: ' + res.status);
            }
            return res.json();
        })
        .catch(err => {
            console.error('Error guardando datos:', err);
            showGlobalError(`Error al guardar datos: ${err.message || 'Error desconocido'}. Por favor, intenta nuevamente.`);
            throw err;
        });
    }

    function setupNavigationButtons() {
        nextButtons.forEach(btn => {
            btn.addEventListener('click', e => {
                e.preventDefault();
                let valid = false;
                if (currentStep === 0) {
                    valid = validateIdentificationForm();
                    // Validar que el checkbox de términos esté seleccionado
                    const termsCheckbox = document.getElementById('id_terms_accepted');
                    const termsError = document.getElementById('id_terms_accepted-error');
                    if (!termsCheckbox || !termsCheckbox.checked) {
                        if (termsError) {
                            termsError.textContent = 'Debes aceptar los términos y condiciones y las Políticas de Privacidad para continuar.';
                            termsError.classList.remove('hidden');
                        }
                        valid = false;
                    } else {
                        if (termsError) {
                            termsError.textContent = '';
                            termsError.classList.add('hidden');
                        }
                    }
                    if (valid) {
                        saveDataToServerSession().then(response => {
                            if (response && response.status === 'success') {
                                goToNextStep();
                            } else {
                                console.error('Error al guardar datos de identificación');
                            }
                        }).catch(error => {
                            console.error('Error en la solicitud:', error);
                        });
                    }
                } else if (currentStep === 1) {
                    valid = validateShippingForm();
                    if (valid) {
                        saveDataToServerSession().then(response => {
                            if (response && response.status === 'success') {
                                goToNextStep();
                            } else {
                                console.error('Error al guardar datos de envío');
                            }
                        }).catch(error => {
                            console.error('Error en la solicitud:', error);
                        });
                    }
                } else {
                    valid = true;
                    goToNextStep();
                }
            });
        });

        prevButtons.forEach(btn => {
            btn.addEventListener('click', e => {
                e.preventDefault();
                goToPrevStep();
            });
        });

        if (paymentBtn) {
            paymentBtn.addEventListener('click', function(e) {
                e.preventDefault();
                saveDataToServerSession().then(response => {
                    if (response && response.status === 'success') {
                        let csrfToken = getCookie('csrftoken');

                        if (!csrfToken) {
                            const metaTag = document.querySelector('meta[name="csrf-token"]');
                            if (metaTag) {
                                csrfToken = metaTag.getAttribute('content');
                                console.log('Token CSRF para pago obtenido desde meta tag');
                            }

                            if (!csrfToken) {
                                const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
                                if (csrfInput) {
                                    csrfToken = csrfInput.value;
                                    console.log('Token CSRF para pago obtenido desde input hidden');
                                }
                            }
                        }

                        if (!csrfToken) {
                            showGlobalError('Error de autenticación. Por favor, intenta las siguientes soluciones: 1) Recarga la página, 2) Borra las cookies del navegador, 3) Usa otro navegador, o 4) Desactiva extensiones que puedan estar bloqueando cookies.');
                            return;
                        }

                        console.log('Iniciando proceso de pago con token CSRF:', csrfToken.substring(0, 5) + '...');

                        fetch('/orders/create-payment/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken
                            },
                            credentials: 'same-origin'
                        })
                        .then(response => {
                            if (!response.ok) {
                                if (response.status === 403) {
                                    showGlobalError('Error de autenticación. Por favor, recarga la página para continuar. Si el problema persiste, borra las cookies del navegador e inténtalo de nuevo.');
                                    throw new Error('Error de autenticación. Token CSRF inválido o expirado.');
                                }
                                throw new Error('Error en la solicitud: ' + response.status);
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.error) {
                                showGlobalError(data.error);
                            } else if (data.init_point) {
                                currentStep = 3; // Marcar como completado
                                updateProgressBar();
                                window.location.href = data.init_point;
                            } else {
                                showGlobalError('Error al procesar el pago. Intente nuevamente.');
                            }
                        })
                        .catch(error => {
                            console.error('Error en proceso de pago:', error);
                            showGlobalError(error.message || 'Error al procesar el pago. Intente nuevamente.');
                        });
                    } else {
                        Swal.fire({icon: 'warning', title: 'Datos incompletos', text: 'Por favor complete todos los datos requeridos.'});
                    }
                }).catch(error => {
                    Swal.fire({icon: 'error', title: 'Error', text: error.message || error.toString()});
                });
            });
        }
    }

    function goToNextStep() {
        if (currentStep < checkoutSteps.length - 1) {
            currentStep++;
            showStep(currentStep);
            updateProgressBar();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    function goToPrevStep() {
        if (currentStep > 0) {
            currentStep--;
            showStep(currentStep);
            updateProgressBar();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    function showFieldError(field, message) {
        if (!field) return;
        field.classList.add('border-red-500');
        const parent = field.parentNode;
        let errorElement = parent.querySelector('.field-error');
        if (!errorElement) {
            errorElement = document.createElement('p');
            errorElement.id = `${field.id}-error`;
            errorElement.className = 'mt-1 text-xs text-red-500 field-error';
            errorElement.setAttribute('role', 'alert');
            parent.appendChild(errorElement);
        }
        errorElement.textContent = message;
    }

    function removeFieldError(field) {
        if (!field) return;
        field.classList.remove('border-red-500');
        const parent = field.parentNode;
        const errorElement = parent.querySelector('.field-error');
        if (errorElement) errorElement.remove();
    }

    function initMultiStepForm() {
        showStep(currentStep);
        updateProgressBar();
        setupNavigationButtons();

        console.log('Formulario multi-paso inicializado');
        console.log('Pasos totales:', checkoutSteps.length);
        console.log('Botones siguiente:', nextButtons.length);
        console.log('Botones anterior:', prevButtons.length);

        window.diagnosticarCSRF = function() {
            console.group('Diagnóstico de CSRF y Cookies');

            const cookiesEnabled = areCookiesEnabled();
            console.log('Cookies habilitadas:', cookiesEnabled);

            console.log('Contenido de document.cookie:', document.cookie);

            const csrfFromCookie = getCookie('csrftoken');
            console.log('Token CSRF desde cookie:', csrfFromCookie);

            const metaTag = document.querySelector('meta[name="csrf-token"]');
            const csrfFromMeta = metaTag ? metaTag.getAttribute('content') : null;
            console.log('Token CSRF desde meta tag:', csrfFromMeta);

            const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
            const csrfFromInput = csrfInput ? csrfInput.value : null;
            console.log('Token CSRF desde input hidden:', csrfFromInput);

            console.log('Instrucciones para verificar propiedades de cookies:');
            console.log('1. Abre la pestaña "Application" en las herramientas de desarrollo');
            console.log('2. Selecciona "Cookies" en el panel izquierdo');
            console.log('3. Verifica que la cookie csrftoken exista y tenga SameSite=Lax o Strict');

            console.groupEnd();

            return {
                cookiesEnabled,
                csrfFromCookie,
                csrfFromMeta,
                csrfFromInput,
                allCookies: document.cookie
            };
        };

        console.log('Función de diagnóstico disponible. Ejecuta "diagnosticarCSRF()" en la consola para verificar el estado de CSRF.');
    }

    initMultiStepForm();
});