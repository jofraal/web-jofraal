/**
 * Script para manejar la interacción del formulario de checkout en dos pasos
 * (identificación y envío) y la validación de los campos.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Elementos del formulario
    const stepIdentification = document.getElementById('step-identification');
    const stepShipping = document.getElementById('step-shipping');
    const backBtn = document.getElementById('back-to-identification');
    const identificationForm = document.getElementById('identification-form');
    const invoiceCheckbox = document.getElementById('id_invoice_requested');
    const documentTypeField = document.getElementById('id_document_type')?.closest('div');
    const documentNumberField = document.getElementById('id_document_number')?.closest('div');

    // Inicialmente ocultar los campos de documento
    if (documentTypeField && documentNumberField) {
        documentTypeField.style.display = 'none';
        documentNumberField.style.display = 'none';
    }

    // Mostrar/ocultar campos de documento cuando se selecciona la opción de factura
    if (invoiceCheckbox) {
        invoiceCheckbox.addEventListener('change', function() {
            if (documentTypeField && documentNumberField) {
                documentTypeField.style.display = this.checked ? 'block' : 'none';
                documentNumberField.style.display = this.checked ? 'block' : 'none';
            }
        });

        // Verificar estado inicial
        if (invoiceCheckbox.checked && documentTypeField && documentNumberField) {
            documentTypeField.style.display = 'block';
            documentNumberField.style.display = 'block';
        }
    }

    // Manejar el botón de volver al paso de identificación
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            if (stepShipping && stepIdentification) {
                stepShipping.classList.add('hidden');
                stepIdentification.classList.remove('hidden');
            }
        });
    }

    // Validación del formulario de identificación
    if (identificationForm) {
        identificationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validar campos requeridos
            const email = document.getElementById('id_email').value;
            const firstName = document.getElementById('id_first_name').value;
            const lastName = document.getElementById('id_last_name').value;
            const phone = document.getElementById('id_phone').value;
            const terms = document.getElementById('id_terms_accepted').checked;
            
            let isValid = true;
            let errorMessage = '';
            
            if (!email) {
                isValid = false;
                errorMessage += 'El correo electrónico es obligatorio. ';
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                isValid = false;
                errorMessage += 'El formato del correo electrónico no es válido. ';
            }
            
            if (!firstName) {
                isValid = false;
                errorMessage += 'El nombre es obligatorio. ';
            }
            
            if (!lastName) {
                isValid = false;
                errorMessage += 'Los apellidos son obligatorios. ';
            }
            
            if (!phone) {
                isValid = false;
                errorMessage += 'El teléfono es obligatorio. ';
            }
            
            if (!terms) {
                isValid = false;
                errorMessage += 'Debe aceptar los términos y condiciones para continuar. ';
                // Resaltar visualmente el checkbox de términos y condiciones
                document.getElementById('id_terms_accepted').parentElement.classList.add('border', 'border-red-500', 'p-2', 'rounded');
            } else {
                // Quitar resaltado si está marcado
                document.getElementById('id_terms_accepted').parentElement.classList.remove('border', 'border-red-500', 'p-2', 'rounded');
            }
            
            // Si se solicita factura, validar campos de documento
            if (invoiceCheckbox && invoiceCheckbox.checked) {
                const documentType = document.getElementById('id_document_type').value;
                const documentNumber = document.getElementById('id_document_number').value;
                
                if (!documentType) {
                    isValid = false;
                    errorMessage += 'El tipo de documento es obligatorio para factura. ';
                }
                
                if (!documentNumber) {
                    isValid = false;
                    errorMessage += 'El número de documento es obligatorio para factura. ';
                }
            }
            
            if (!isValid) {
                // Mostrar mensaje de error
                alert(errorMessage);
                return;
            }
            
            // Si todo está bien, enviar el formulario
            this.submit();
        });
    }
});