/**
 * Script para validación en tiempo real del formulario de checkout
 * Proporciona feedback inmediato al usuario durante el proceso de compra
 */
document.addEventListener('DOMContentLoaded', function() {
    // Elementos del formulario de identificación
    const identificationForm = document.getElementById('identification-form');
    const emailField = document.getElementById('id_email');
    const firstNameField = document.getElementById('id_first_name');
    const lastNameField = document.getElementById('id_last_name');
    const phoneField = document.getElementById('id_phone');
    const termsCheckbox = document.getElementById('id_terms_accepted');
    
    // Elementos del formulario de envío
    const shippingForm = document.getElementById('shipping-form');
    const departmentField = document.getElementById('id_department');
    const provinceField = document.getElementById('id_province');
    const districtField = document.getElementById('id_district');
    const cityField = document.getElementById('id_city');
    const streetField = document.getElementById('id_street');
    const streetNumberField = document.getElementById('id_street_number');
    const recipientField = document.getElementById('id_recipient');
    const cardholderEmailField = document.getElementById('cardholderEmail');
    
    // Función para validar email
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Función para validar teléfono (9 dígitos para Perú)
    function isValidPhone(phone) {
        const phoneRegex = /^[0-9]{9}$/;
        return phoneRegex.test(phone.replace(/\s+/g, ''));
    }
    
    // Función para mostrar error en un campo
    function showFieldError(field, message) {
        // Eliminar mensajes de error anteriores
        const parent = field.parentNode;
        const existingError = parent.querySelector('.field-error');
        if (existingError) parent.removeChild(existingError);
        
        // Añadir clase de error al campo
        field.classList.add('border-red-500');
        
        // Crear y añadir mensaje de error
        const errorElement = document.createElement('p');
        errorElement.className = 'mt-1 text-xs text-red-500 field-error';
        errorElement.textContent = message;
        parent.appendChild(errorElement);
    }
    
    // Función para eliminar error de un campo
    function removeFieldError(field) {
        field.classList.remove('border-red-500');
        const parent = field.parentNode;
        const existingError = parent.querySelector('.field-error');
        if (existingError) parent.removeChild(existingError);
    }
    
    // Validación en tiempo real para el email
    if (emailField) {
        emailField.addEventListener('blur', function() {
            const email = this.value.trim();
            if (!email) {
                showFieldError(this, 'El correo electrónico es obligatorio');
            } else if (!isValidEmail(email)) {
                showFieldError(this, 'Ingrese un correo electrónico válido');
            } else {
                removeFieldError(this);
            }
        });
    }
    
    // Validación en tiempo real para el teléfono
    if (phoneField) {
        phoneField.addEventListener('blur', function() {
            const phone = this.value.trim();
            if (!phone) {
                showFieldError(this, 'El teléfono es obligatorio');
            } else if (!isValidPhone(phone)) {
                showFieldError(this, 'Ingrese un número de teléfono válido (9 dígitos)');
            } else {
                removeFieldError(this);
            }
        });
    }
    
    // Validación en tiempo real para campos de texto obligatorios
    const requiredTextFields = [
        { field: firstNameField, name: 'nombre' },
        { field: lastNameField, name: 'apellidos' },
        { field: streetField, name: 'calle' },
        { field: streetNumberField, name: 'número' },
        { field: recipientField, name: 'destinatario' }
    ];
    
    requiredTextFields.forEach(item => {
        if (item.field) {
            item.field.addEventListener('blur', function() {
                if (!this.value.trim()) {
                    showFieldError(this, `El ${item.name} es obligatorio`);
                } else {
                    removeFieldError(this);
                }
            });
        }
    });
    
    // Validación del formulario de identificación al enviar
    if (identificationForm) {
        identificationForm.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Validar email
            if (emailField) {
                const email = emailField.value.trim();
                if (!email) {
                    showFieldError(emailField, 'El correo electrónico es obligatorio');
                    isValid = false;
                } else if (!isValidEmail(email)) {
                    showFieldError(emailField, 'Ingrese un correo electrónico válido');
                    isValid = false;
                }
            }
            
            // Validar nombre y apellidos
            if (firstNameField && !firstNameField.value.trim()) {
                showFieldError(firstNameField, 'El nombre es obligatorio');
                isValid = false;
            }
            
            if (lastNameField && !lastNameField.value.trim()) {
                showFieldError(lastNameField, 'Los apellidos son obligatorios');
                isValid = false;
            }
            
            // Validar teléfono
            if (phoneField) {
                const phone = phoneField.value.trim();
                if (!phone) {
                    showFieldError(phoneField, 'El teléfono es obligatorio');
                    isValid = false;
                } else if (!isValidPhone(phone)) {
                    showFieldError(phoneField, 'Ingrese un número de teléfono válido (9 dígitos)');
                    isValid = false;
                }
            }
            
            // Validar términos y condiciones
            if (termsCheckbox && !termsCheckbox.checked) {
                const termsContainer = termsCheckbox.closest('div');
                termsContainer.classList.add('p-2', 'border', 'border-red-500', 'rounded');
                isValid = false;
            }
            
            if (!isValid) {
                e.preventDefault();
                // Scroll al primer campo con error
                const firstErrorField = document.querySelector('.border-red-500');
                if (firstErrorField) {
                    firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstErrorField.focus();
                }
            }
        });
    }
    
    // Validación del formulario de envío
    if (shippingForm) {
        // Validar campos al perder el foco
        const shippingRequiredFields = [
            { field: departmentField, name: 'departamento' },
            { field: provinceField, name: 'provincia' },
            { field: districtField, name: 'distrito' },
            { field: cityField, name: 'ciudad' },
            { field: streetField, name: 'calle' },
            { field: streetNumberField, name: 'número' },
            { field: recipientField, name: 'destinatario' },
            { field: cardholderEmailField, name: 'correo' }
        ];
        
        shippingRequiredFields.forEach(item => {
            if (item.field) {
                item.field.addEventListener('blur', function() {
                    if (!this.value.trim()) {
                        showFieldError(this, `El ${item.name} es obligatorio`);
                    } else if (item.field === cardholderEmailField && !isValidEmail(this.value.trim())) {
                        showFieldError(this, 'Ingrese un correo electrónico válido');
                    } else {
                        removeFieldError(this);
                    }
                });
            }
        });
    }
});