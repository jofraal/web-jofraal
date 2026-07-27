/**
 * Script para autocompletar datos de usuario en el checkout
 * Permite cargar datos personales y direcciones guardadas del usuario
 */
document.addEventListener('DOMContentLoaded', function() {
    // Elementos del formulario de identificación
    const identificationForm = document.getElementById('identification-form');
    const shippingForm = document.getElementById('shipping-form');
    
    // Contenedor para el botón de autocompletar
    const identificationStep = document.getElementById('step-identification');
    let shippingStep = document.getElementById('step-shipping');
    
    // Verificar si el usuario está autenticado
    const isAuthenticated = document.body.classList.contains('user-authenticated');
    console.log('Usuario autenticado:', isAuthenticated);
    
    if (isAuthenticated && identificationStep) {
        const existingContainer = identificationStep.querySelector('.autofill-container');
        if (!existingContainer) {
            const autofillContainer = document.createElement('div');
            autofillContainer.className = 'p-3 mb-4 bg-indigo-50 rounded-md border border-indigo-200 autofill-container';
            
            const autofillTitle = document.createElement('h3');
            autofillTitle.className = 'mb-2 text-sm font-medium text-indigo-800';
            autofillTitle.textContent = '¿Quieres usar tus datos guardados?';
            
            const autofillButton = document.createElement('button');
            autofillButton.type = 'button';
            autofillButton.className = 'flex items-center px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md transition duration-300 hover:bg-indigo-700';
            autofillButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="mr-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> Usar mis datos personales';
            
            autofillButton.addEventListener('click', fetchAndFillUserData);
            
            autofillContainer.appendChild(autofillTitle);
            autofillContainer.appendChild(autofillButton);
            
            const titleElement = identificationStep.querySelector('h2').parentNode;
            titleElement.parentNode.insertBefore(autofillContainer, titleElement.nextSibling);
        }
    }
    
    // Función para inicializar el contenedor de direcciones guardadas
    function initializeSavedAddresses() {
        shippingStep = document.getElementById('step-shipping'); // Reintentar obtener el elemento
        console.log('Elemento step-shipping encontrado:', !!shippingStep);
        
        if (isAuthenticated && shippingStep) {
            const existingHtmlAddressContainer = shippingStep.querySelector('.bg-gray-50 h3');
            
            if (!existingHtmlAddressContainer) {
                const existingAddressContainer = shippingStep.querySelector('#saved-addresses-container');
                
                if (!existingAddressContainer) {
                    console.log('Creando contenedor de direcciones guardadas');
                    const addressContainer = document.createElement('div');
                    addressContainer.className = 'p-4 mb-5 bg-indigo-50 rounded-lg border border-indigo-200 shadow-sm transition-all duration-300 hover:shadow';
                    addressContainer.id = 'saved-addresses-container';
                    
                    const addressTitle = document.createElement('h3');
                    addressTitle.className = 'mb-3 text-sm font-medium text-indigo-800';
                    addressTitle.textContent = '¿Quieres usar una dirección guardada?';
                    
                    const addressButton = document.createElement('button');
                    addressButton.type = 'button';
                    addressButton.className = 'flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md shadow-sm transition duration-300 hover:bg-indigo-700 hover:shadow';
                    addressButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="mr-2 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> Cargar mis direcciones';
                    
                    addressButton.addEventListener('click', fetchAndShowAddresses);
                    
                    addressContainer.appendChild(addressTitle);
                    addressContainer.appendChild(addressButton);
                    
                    const titleElement = shippingStep.querySelector('h2').parentNode;
                    titleElement.parentNode.insertBefore(addressContainer, titleElement.nextSibling);
                } else {
                    console.log('Contenedor de direcciones guardadas ya existe');
                }
            } else {
                console.log('Contenedor renderizado por el servidor encontrado (.bg-gray-50 h3)');
                const existingAddressSelect = shippingStep.querySelector('select[name="saved_address"]');
                if (existingAddressSelect) {
                    const addressContainer = existingAddressSelect.closest('.bg-gray-50');
                    if (addressContainer) {
                        const existingButton = addressContainer.querySelector('.load-addresses-btn');
                        if (!existingButton) {
                            const addressButton = document.createElement('button');
                            addressButton.type = 'button';
                            addressButton.className = 'flex items-center px-4 py-2 mt-2 text-sm font-medium text-white bg-indigo-600 rounded-md shadow-sm transition duration-300 hover:bg-indigo-700 hover:shadow load-addresses-btn';
                            addressButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="mr-2 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> Cargar mis direcciones';
                            
                            addressButton.addEventListener('click', fetchAndShowAddresses);
                            
                            addressContainer.appendChild(addressButton);
                        }
                    }
                }
            }
        } else {
            console.log('No se puede inicializar direcciones guardadas: usuario no autenticado o step-shipping no encontrado');
        }
    }
    
    // Ejecutar la inicialización al cargar el DOM
    initializeSavedAddresses();
    
    // Escuchar cambios en el DOM (por si el paso de envío se muestra dinámicamente)
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (document.getElementById('step-shipping') && !document.getElementById('saved-addresses-container')) {
                console.log('step-shipping detectado dinámicamente, inicializando direcciones guardadas');
                initializeSavedAddresses();
            }
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
    
    // Escuchar evento personalizado del cambio de paso (si multi_step_checkout.js lo dispara)
    document.addEventListener('stepChanged', (e) => {
        if (e.detail.step === 'shipping') {
            console.log('Cambio de paso a shipping detectado, inicializando direcciones guardadas');
            initializeSavedAddresses();
        }
    });
    
    // Función para obtener y rellenar los datos del usuario
    function fetchAndFillUserData() {
        fetch('/orders/api/user-data/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error al obtener datos del usuario');
                }
                return response.json();
            })
            .then(data => {
                fillIdentificationForm(data);
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('No se pudieron cargar tus datos. Por favor, inténtalo de nuevo.', 'error');
            });
    }
    
    // Función para rellenar el formulario de identificación
    function fillIdentificationForm(userData) {
        if (!identificationForm) return;
        
        const emailField = document.getElementById('id_email');
        const firstNameField = document.getElementById('id_first_name');
        const lastNameField = document.getElementById('id_last_name');
        const phoneField = document.getElementById('id_phone');
        const documentTypeField = document.getElementById('id_document_type');
        const documentNumberField = document.getElementById('id_document_number');
        
        if (emailField && userData.email) emailField.value = userData.email;
        if (firstNameField && userData.first_name) firstNameField.value = userData.first_name;
        if (lastNameField && userData.last_name) lastNameField.value = userData.last_name;
        if (phoneField && userData.phone_number) phoneField.value = userData.phone_number;
        if (documentTypeField && userData.document_type) documentTypeField.value = userData.document_type;
        if (documentNumberField && userData.document_number) documentTypeField.value = userData.document_number;
        
        showNotification('Datos personales cargados correctamente', 'success');
    }
    
    // Función para obtener y mostrar las direcciones guardadas
    let hasFetchedAddresses = false;
    let fetchCount = 0;
    function fetchAndShowAddresses() {
        fetchCount++;
        console.log(`Ejecución #${fetchCount} de fetchAndShowAddresses`);
        
        if (window.loadingAddresses || hasFetchedAddresses) {
            console.log('fetchAndShowAddresses bloqueado: ya se está cargando o ya se cargó');
            return;
        }
        
        hasFetchedAddresses = true;
        window.loadingAddresses = true;
        
        const container = document.querySelector('.bg-gray-50') || document.getElementById('saved-addresses-container');
        if (container) {
            const loadingMsg = document.createElement('p');
            loadingMsg.className = 'mt-2 text-sm text-indigo-600 loading-indicator';
            loadingMsg.textContent = 'Cargando direcciones...';
            container.appendChild(loadingMsg);
        }
        
        fetch('/orders/api/user-addresses/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error al obtener direcciones');
                }
                return response.json();
            })
            .then(addresses => {
                console.log('Direcciones recibidas de la API:', addresses);
                const uniqueAddresses = [];
                const seen = new Set();
                addresses.forEach(addr => {
                    const key = `${addr.street}-${addr.street_number}-${addr.district}-${addr.province}-${addr.department}-${addr.additional_info || ''}`;
                    if (!seen.has(key)) {
                        seen.add(key);
                        uniqueAddresses.push(addr);
                    }
                });
                
                uniqueAddresses.sort((a, b) => {
                    if (a.is_default && !b.is_default) return -1;
                    if (!a.is_default && b.is_default) return 1;
                    return 0;
                });
                
                const defaultAddress = uniqueAddresses.find(addr => addr.is_default);
                if (defaultAddress) {
                    fillShippingForm(defaultAddress);
                }
                
                const loadingIndicator = document.querySelector('.loading-indicator');
                if (loadingIndicator) {
                    loadingIndicator.remove();
                }
                
                displayAddresses(uniqueAddresses);
                window.loadingAddresses = false;
                
                const event = new CustomEvent('addressesRendered', { detail: { addresses: uniqueAddresses } });
                window.dispatchEvent(event);
            })
            .catch(error => {
                console.error('Error al obtener direcciones:', error);
                showNotification('No se pudieron cargar tus direcciones. Por favor, inténtalo de nuevo.', 'error');
                
                const loadingIndicator = document.querySelector('.loading-indicator');
                if (loadingIndicator) {
                    loadingIndicator.remove();
                }
                
                window.loadingAddresses = false;
            });
    }
    
    // Función para mostrar las direcciones guardadas
    function displayAddresses(addresses) {
        let container = document.querySelector('.bg-gray-50');
        let isDynamicContainer = false;
        
        if (!container || !container.querySelector('h3')) {
            container = document.getElementById('saved-addresses-container');
            isDynamicContainer = true;
        }
        
        if (!container) {
            console.error('No se encontró contenedor para las direcciones');
            return;
        }
        
        if (isDynamicContainer) {
            const title = container.querySelector('h3');
            const button = container.querySelector('button');
            container.innerHTML = '';
            if (title) container.appendChild(title);
            if (button) container.appendChild(button);
        } else {
            const addressList = container.querySelector('.address-list');
            if (addressList) {
                addressList.remove();
            }
        }
        
        if (!addresses || addresses.length === 0) {
            const noAddressesMsg = document.createElement('p');
            noAddressesMsg.className = 'mt-2 text-sm text-gray-600';
            noAddressesMsg.textContent = 'No tienes direcciones guardadas.';
            container.appendChild(noAddressesMsg);
            return;
        }
        
        const addressList = document.createElement('div');
        addressList.className = 'mt-3 space-y-2 address-list';
        
        const infoMsg = document.createElement('p');
        infoMsg.className = 'mb-2 text-xs italic text-indigo-600';
        infoMsg.textContent = 'La dirección predeterminada se carga automáticamente';
        container.appendChild(infoMsg);
        
        addresses.forEach(address => {
            const addressCard = document.createElement('div');
            addressCard.className = `flex justify-between items-center p-2 rounded border ${address.is_default ? 'bg-indigo-50 border-indigo-300' : 'bg-white border-gray-200'}`;
            
            const addressInfo = document.createElement('div');
            addressInfo.className = 'flex-1';
            
            const addressHeader = document.createElement('div');
            addressHeader.className = 'flex items-center';
            
            const addressType = document.createElement('span');
            addressType.className = 'text-xs font-medium text-indigo-700';
            addressType.textContent = address.address_type_display || 'Dirección';
            
            if (address.is_default) {
                const defaultBadge = document.createElement('span');
                defaultBadge.className = 'px-1.5 py-0.5 ml-2 text-xs text-indigo-800 bg-indigo-100 rounded-full';
                defaultBadge.textContent = 'Predeterminada';
                addressHeader.appendChild(addressType);
                addressHeader.appendChild(defaultBadge);
            } else {
                addressHeader.appendChild(addressType);
            }
            
            const addressText = document.createElement('span');
            addressText.className = 'block mt-1 text-sm text-gray-700';
            addressText.textContent = `${address.street} ${address.street_number}, ${address.district}, ${address.province}, ${address.department}`;
            
            addressInfo.appendChild(addressHeader);
            addressInfo.appendChild(addressText);
            
            const useButton = document.createElement('button');
            useButton.type = 'button';
            useButton.className = 'px-2 py-1 ml-2 text-xs font-medium text-indigo-700 bg-indigo-100 rounded hover:bg-indigo-200';
            useButton.textContent = 'Usar';
            useButton.addEventListener('click', function() {
                fillShippingForm(address);
            });
            
            addressCard.appendChild(addressInfo);
            addressCard.appendChild(useButton);
            
            addressList.appendChild(addressCard);
        });
        
        container.appendChild(addressList);
    }
    
    // Función para rellenar el formulario de envío con una dirección
    function fillShippingForm(address) {
        if (!shippingForm) return;
        
        const departmentField = document.getElementById('id_department');
        const provinceField = document.getElementById('id_province');
        const districtField = document.getElementById('id_district');
        const cityField = document.getElementById('id_city');
        const streetField = document.getElementById('id_street');
        const streetNumberField = document.getElementById('id_street_number');
        const additionalInfoField = document.getElementById('id_additional_info');
        const countryField = document.getElementById('id_country');
        const latitudeField = document.getElementById('id_latitude');
        const longitudeField = document.getElementById('id_longitude');
        
        if (departmentField && address.department) {
            departmentField.value = address.department;
            const event = new Event('change', { bubbles: true });
            departmentField.dispatchEvent(event);
            
            setTimeout(() => {
                if (provinceField && address.province) {
                    provinceField.value = address.province;
                    provinceField.dispatchEvent(event);
                    
                    setTimeout(() => {
                        if (districtField && address.district) {
                            districtField.value = address.district;
                            // Disparar evento change para actualizar el mapa
                            districtField.dispatchEvent(event);
                        }
                    }, 500);
                }
            }, 500);
        }
        
        if (cityField) {
            cityField.value = address.city || address.district || '';
        }
        
        if (streetField) {
            streetField.value = address.street || '';
            // Disparar evento change para actualizar el mapa
            const event = new Event('change', { bubbles: true });
            streetField.dispatchEvent(event);
        }
        
        if (streetNumberField) {
            streetNumberField.value = address.street_number || '';
        }
        
        if (additionalInfoField) {
            additionalInfoField.value = address.additional_info || '';
        }
        
        if (countryField) {
            countryField.value = address.country || 'Perú';
        }
        
        // Actualizar coordenadas
        if (latitudeField && address.latitude) latitudeField.value = address.latitude;
        if (longitudeField && address.longitude) longitudeField.value = address.longitude;
        
        // Actualizar el mapa si está disponible
        setTimeout(() => {
            // Verificar si existe la función updateMapFromAddress (definida en map_checkout.js)
            if (typeof updateMapFromAddress === 'function') {
                console.log('Actualizando mapa con dirección guardada');
                updateMapFromAddress();
            } else if (window.map && window.marker && address.latitude && address.longitude) {
                // Si no está disponible la función pero sí el mapa, actualizar manualmente
                console.log('Actualizando mapa manualmente con coordenadas:', address.latitude, address.longitude);
                const position = { lat: parseFloat(address.latitude), lng: parseFloat(address.longitude) };
                window.map.setCenter(position);
                window.marker.setPosition(position);
            }
        }, 1000);
        
        showNotification('Dirección cargada correctamente', 'success');
    }
    
    // Función para mostrar notificaciones
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-3 rounded-md shadow-md z-50 ${type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' : 'bg-green-100 text-green-800 border border-green-200'}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('opacity-0', 'transition-opacity', 'duration-500');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500);
        }, 3000);
    }
});