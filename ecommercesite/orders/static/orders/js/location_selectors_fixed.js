/**
 * Versión optimizada y mejorada de los selectores de ubicación
 * Implementa caché, precarga inteligente, indicadores visuales de carga,
 * reintentos automáticos, debounce para evitar múltiples solicitudes,
 * y validación en tiempo real para los campos de ubicación
 */
document.addEventListener('DOMContentLoaded', function() {
    // Elementos del formulario
    const departmentSelect = document.getElementById('id_department');
    const provinceSelect = document.getElementById('id_province');
    const districtSelect = document.getElementById('id_district');

    if (!departmentSelect || !provinceSelect || !districtSelect) {
        console.error('No se encontraron los selectores de ubicación');
        return;
    }

    // Caché para almacenar datos y reducir llamadas a la API
    const cache = {
        departments: [],
        provinces: {},
        districts: {},
        popularDepartments: ['Lima', 'Arequipa', 'Cusco', 'La Libertad', 'Piura'] // Departamentos populares para precarga
    };
    
    // Configuración para reintentos y debounce
    const config = {
        maxRetries: 3,        // Número máximo de reintentos para solicitudes fallidas
        retryDelay: 1000,     // Tiempo de espera entre reintentos (ms)
        debounceDelay: 300,   // Tiempo de espera para debounce (ms)
        preloadThreshold: 0.8 // Umbral de probabilidad para precarga (0-1)
    };
    
    // Estado de la interfaz
    const uiState = {
        isValid: false,       // Estado de validación del formulario
        loadingStates: {},    // Estados de carga para cada selector
        retryCount: {}        // Contador de reintentos para cada solicitud
    };

    // Función para mostrar mensajes de error en los selectores
    function showError(select, message, isRetryable = false) {
        select.innerHTML = isRetryable ? 
            `<option value="">${message} (Clic para reintentar)</option>` : 
            `<option value="">${message}</option>`;
        select.disabled = !isRetryable;
        select.classList.add('border-red-300');
        
        // Actualizar estado de validación
        validateLocationFields();
    }

    // Función para restablecer un selector
    function resetSelect(select, defaultText = '') {
        select.innerHTML = `<option value="">${defaultText}</option>`;
        select.disabled = true;
        select.classList.remove('border-red-300');
        select.classList.remove('border-green-300');
        select.classList.remove('animate-pulse');
        
        // Actualizar estado de validación
        validateLocationFields();
    }
    
    // Función para mostrar estado de carga con animación
    function showLoading(select, message = 'Cargando...') {
        select.innerHTML = `<option value="">${message}</option>`;
        select.disabled = true;
        select.classList.remove('border-red-300');
        select.classList.remove('border-green-300');
        select.classList.add('animate-pulse');
        
        // Registrar estado de carga
        uiState.loadingStates[select.id] = true;
    }
    
    // Función para marcar un campo como válido
    function markAsValid(select) {
        if (select.value) {
            select.classList.add('border-green-300');
        } else {
            select.classList.remove('border-green-300');
        }
    }
    
    // Función para validar todos los campos de ubicación
    function validateLocationFields() {
        const allSelected = departmentSelect.value && provinceSelect.value && districtSelect.value;
        const anyLoading = Object.values(uiState.loadingStates).some(state => state === true);
        const anyError = [departmentSelect, provinceSelect, districtSelect].some(select => 
            select.classList.contains('border-red-300'));
        
        uiState.isValid = allSelected && !anyLoading && !anyError;
        
        // Actualizar UI basado en validación
        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = !uiState.isValid;
            if (uiState.isValid) {
                submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
            } else {
                submitButton.classList.add('opacity-50', 'cursor-not-allowed');
            }
        }
        
        return uiState.isValid;
    }
    
    // Función para implementar debounce
    function debounce(func, delay) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // Función para cargar los departamentos con reintentos automáticos
    function loadDepartments(retry = 0) {
        // Reiniciar contador de reintentos si es una nueva solicitud
        if (retry === 0) {
            uiState.retryCount['departments'] = 0;
        }
        
        // Si ya tenemos departamentos en caché, usarlos
        if (cache.departments.length > 0) {
            populateDepartments(cache.departments);
            return;
        }

        // Mostrar estado de carga con animación
        showLoading(departmentSelect, retry > 0 ? `Reintentando (${retry})...` : 'Cargando...');

        fetch('/orders/api/departments/')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(departments => {
                // Guardar en caché
                cache.departments = departments;
                populateDepartments(departments);
                
                // Actualizar estado de carga
                uiState.loadingStates[departmentSelect.id] = false;
                
                // Precarga inteligente de provincias para departamentos populares
                preloadPopularProvinces(departments);
            })
            .catch(error => {
                console.error('Error al cargar departamentos:', error);
                uiState.retryCount['departments'] = (uiState.retryCount['departments'] || 0) + 1;
                
                if (retry < config.maxRetries) {
                    // Reintentar después de un retraso
                    setTimeout(() => loadDepartments(retry + 1), config.retryDelay);
                } else {
                    // Mostrar error con opción de reintentar
                    showError(departmentSelect, 'Error al cargar', true);
                    resetSelect(provinceSelect, 'Seleccione un departamento primero');
                    resetSelect(districtSelect, 'Seleccione una provincia primero');
                    
                    // Actualizar estado de carga
                    uiState.loadingStates[departmentSelect.id] = false;
                }
            });
    }

    // Función para poblar el selector de departamentos
    function populateDepartments(departments) {
        departmentSelect.innerHTML = '<option value="">Seleccione un departamento</option>';
        departmentSelect.disabled = false;
        departmentSelect.classList.remove('animate-pulse');

        departments.forEach(department => {
            const option = document.createElement('option');
            option.value = department;
            option.textContent = department;
            
            // Destacar departamentos populares
            if (cache.popularDepartments.includes(department)) {
                option.classList.add('font-semibold');
            }
            
            departmentSelect.appendChild(option);
        });

        // Si hay un valor preseleccionado, cargar provincias
        if (departmentSelect.value) {
            loadProvinces(departmentSelect.value);
            markAsValid(departmentSelect);
        }
        
        // Actualizar estado de validación
        validateLocationFields();
    }

    // Función para precargar provincias de departamentos populares
    function preloadPopularProvinces(departments) {
        // Solo precargar si tenemos departamentos populares en la lista
        const departmentsToPreload = cache.popularDepartments.filter(dept => 
            departments.includes(dept) && !cache.provinces[dept]);
            
        if (departmentsToPreload.length === 0) return;
        
        // Precargar en segundo plano, uno por uno para no sobrecargar
        let index = 0;
        const preloadNext = () => {
            if (index >= departmentsToPreload.length) return;
            
            const dept = departmentsToPreload[index++];
            console.log(`Precargando provincias para ${dept}...`);
            
            fetch(`/orders/api/provinces/?department=${encodeURIComponent(dept)}`)
                .then(response => response.ok ? response.json() : null)
                .then(provinces => {
                    if (provinces) {
                        cache.provinces[dept] = provinces;
                        console.log(`Provincias para ${dept} precargadas (${provinces.length})`);
                    }
                    // Continuar con el siguiente después de un breve retraso
                    setTimeout(preloadNext, 500);
                })
                .catch(() => setTimeout(preloadNext, 500)); // Continuar incluso si hay error
        };
        
        // Iniciar precarga después de un breve retraso
        setTimeout(preloadNext, 1000);
    }
    
    // Función para cargar las provincias según el departamento seleccionado
    function loadProvinces(department, retry = 0) {
        // Reiniciar contador de reintentos si es una nueva solicitud
        if (retry === 0) {
            uiState.retryCount[`provinces-${department}`] = 0;
        }
        
        if (!department) {
            resetSelect(provinceSelect, 'Seleccione un departamento primero');
            resetSelect(districtSelect, 'Seleccione una provincia primero');
            return;
        }

        // Si ya tenemos provincias en caché para este departamento, usarlas
        if (cache.provinces[department]) {
            populateProvinces(department, cache.provinces[department]);
            return;
        }

        // Mostrar estado de carga con animación
        showLoading(provinceSelect, retry > 0 ? `Reintentando (${retry})...` : 'Cargando...');
        resetSelect(districtSelect, 'Seleccione una provincia primero');

        fetch(`/orders/api/provinces/?department=${encodeURIComponent(department)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(provinces => {
                // Guardar en caché
                cache.provinces[department] = provinces;
                populateProvinces(department, provinces);
                
                // Actualizar estado de carga
                uiState.loadingStates[provinceSelect.id] = false;
            })
            .catch(error => {
                console.error(`Error al cargar provincias para ${department}:`, error);
                uiState.retryCount[`provinces-${department}`] = (uiState.retryCount[`provinces-${department}`] || 0) + 1;
                
                if (retry < config.maxRetries) {
                    // Reintentar después de un retraso
                    setTimeout(() => loadProvinces(department, retry + 1), config.retryDelay);
                } else {
                    // Mostrar error con opción de reintentar
                    showError(provinceSelect, 'Error al cargar', true);
                    resetSelect(districtSelect, 'Seleccione una provincia primero');
                    
                    // Actualizar estado de carga
                    uiState.loadingStates[provinceSelect.id] = false;
                }
            });
    }

    // Función para poblar el selector de provincias
    function populateProvinces(department, provinces) {
        provinceSelect.innerHTML = '<option value="">Seleccione una provincia</option>';
        provinceSelect.disabled = false;
        provinceSelect.classList.remove('animate-pulse');

        // Ordenar provincias alfabéticamente para mejor usabilidad
        provinces.sort((a, b) => a.localeCompare(b));

        provinces.forEach(province => {
            const option = document.createElement('option');
            option.value = province;
            option.textContent = province;
            provinceSelect.appendChild(option);
        });

        // Si hay un valor preseleccionado, cargar distritos
        if (provinceSelect.value) {
            loadDistricts(department, provinceSelect.value);
            markAsValid(provinceSelect);
        }
        
        // Actualizar estado de validación
        validateLocationFields();
    }

    // Función para cargar los distritos según la provincia seleccionada
    function loadDistricts(department, province, retry = 0) {
        // Reiniciar contador de reintentos si es una nueva solicitud
        if (retry === 0) {
            uiState.retryCount[`districts-${department}-${province}`] = 0;
        }
        
        if (!department || !province) {
            resetSelect(districtSelect, 'Seleccione una provincia primero');
            return;
        }

        // Clave para caché
        const cacheKey = `${department}-${province}`;

        // Si ya tenemos distritos en caché para esta combinación, usarlos
        if (cache.districts[cacheKey]) {
            populateDistricts(cache.districts[cacheKey]);
            return;
        }

        // Mostrar estado de carga con animación
        showLoading(districtSelect, retry > 0 ? `Reintentando (${retry})...` : 'Cargando...');

        fetch(`/orders/api/districts/?department=${encodeURIComponent(department)}&province=${encodeURIComponent(province)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(districts => {
                // Guardar en caché
                cache.districts[cacheKey] = districts;
                populateDistricts(districts);
                
                // Actualizar estado de carga
                uiState.loadingStates[districtSelect.id] = false;
            })
            .catch(error => {
                console.error(`Error al cargar distritos para ${province}:`, error);
                uiState.retryCount[`districts-${department}-${province}`] = 
                    (uiState.retryCount[`districts-${department}-${province}`] || 0) + 1;
                
                if (retry < config.maxRetries) {
                    // Reintentar después de un retraso
                    setTimeout(() => loadDistricts(department, province, retry + 1), config.retryDelay);
                } else {
                    // Mostrar error con opción de reintentar
                    showError(districtSelect, 'Error al cargar', true);
                    
                    // Actualizar estado de carga
                    uiState.loadingStates[districtSelect.id] = false;
                }
            });
    }

    // Función para poblar el selector de distritos
    function populateDistricts(districts) {
        districtSelect.innerHTML = '<option value="">Seleccione un distrito</option>';
        districtSelect.disabled = false;
        districtSelect.classList.remove('animate-pulse');

        // Ordenar distritos alfabéticamente para mejor usabilidad
        districts.sort((a, b) => a.localeCompare(b));

        districts.forEach(district => {
            const option = document.createElement('option');
            option.value = district;
            option.textContent = district;
            districtSelect.appendChild(option);
        });
        
        // Si hay un valor seleccionado, marcarlo como válido
        if (districtSelect.value) {
            markAsValid(districtSelect);
        }
        
        // Actualizar estado de validación
        validateLocationFields();
    }

    // Cargar departamentos al iniciar
    loadDepartments();

    // Evento para cuando cambia el departamento (con debounce)
    departmentSelect.addEventListener('change', function() {
        // Marcar como válido si tiene valor
        if (this.value) {
            markAsValid(this.value);
        } else {
            this.classList.remove('border-green-300');
        }
        
        // Cargar provincias con debounce
        debounce(loadProvinces, config.debounceDelay)(this.value);
    });

    // Evento para cuando cambia la provincia (con debounce)
    provinceSelect.addEventListener('change', function() {
        // Marcar como válido si tiene valor
        if (this.value) {
            markAsValid(this.value);
        } else {
            this.classList.remove('border-green-300');
        }
        
        // Cargar distritos con debounce
        debounce(loadDistricts, config.debounceDelay)(departmentSelect.value, this.value);
    });
    
    // Evento para cuando cambia el distrito
    districtSelect.addEventListener('change', function() {
        // Marcar como válido si tiene valor
        if (this.value) {
            markAsValid(this.value);
        } else {
            this.classList.remove('border-green-300');
        }
        
        // Actualizar estado de validación
        validateLocationFields();
    });
    
    // Eventos para reintentar en caso de error
    departmentSelect.addEventListener('click', function() {
        if (this.classList.contains('border-red-300')) {
            loadDepartments();
        }
    });
    
    provinceSelect.addEventListener('click', function() {
        if (this.classList.contains('border-red-300') && departmentSelect.value) {
            loadProvinces(departmentSelect.value);
        }
    });
    
    districtSelect.addEventListener('click', function() {
        if (this.classList.contains('border-red-300') && departmentSelect.value && provinceSelect.value) {
            loadDistricts(departmentSelect.value, provinceSelect.value);
        }
    });
    
    // Validar campos al cargar la página
    setTimeout(validateLocationFields, 1000);
});