document.addEventListener('DOMContentLoaded', function() {
    // Elementos del formulario
    const departmentSelect = document.getElementById('department');
    const provinceSelect = document.getElementById('province');
    const districtSelect = document.getElementById('district');
    
    // Verificar que los elementos existan
    if (!departmentSelect || !provinceSelect || !districtSelect) {
        console.error('No se encontraron los elementos del formulario de dirección');
        return;
    }
    
    // Caché para almacenar datos y reducir llamadas a la API
    const cache = {
        departments: [],
        provinces: {},
        districts: {}
    };
    
    // URLs para las APIs de ubicaciones
    const API_URLS = {
        // URLs principales (módulo users)
        departments: '/users/api/get-departments/',
        provinces: '/users/api/get-provinces/',
        districts: '/users/api/get-districts/',
        // URLs alternativas (módulo orders)
        alt_departments: '/orders/api/get-departments/',
        alt_provinces: '/orders/api/get-provinces/',
        alt_districts: '/orders/api/get-districts/'
    };
    
    // Función para cargar los departamentos
    function loadDepartments() {
        // Si ya tenemos departamentos en caché, usarlos
        if (cache.departments.length > 0) {
            populateDepartments(cache.departments);
            return;
        }

        // Mostrar estado de carga
        departmentSelect.innerHTML = '<option value="">Cargando...</option>';
        departmentSelect.disabled = true;

        console.log('Solicitando departamentos desde:', API_URLS.departments);
        
        // Intentar cargar desde la API principal
        fetchWithFallback(API_URLS.departments, API_URLS.alt_departments)
            .then(departments => {
                console.log(`Departamentos recibidos: ${departments.length}`, departments);
                // Guardar en caché
                cache.departments = departments;
                populateDepartments(departments);
            })
            .catch(error => {
                console.error('Error al cargar departamentos:', error);
                departmentSelect.innerHTML = '<option value="">Error al cargar</option>';
                departmentSelect.disabled = true;
                clearSelect(provinceSelect, 'Seleccione un departamento primero');
                clearSelect(districtSelect, 'Seleccione una provincia primero');
            });
    }
    
    // Función para poblar el selector de departamentos
    function populateDepartments(departments) {
        departmentSelect.innerHTML = '<option value="">Seleccione un departamento</option>';
        departmentSelect.disabled = false;

        departments.forEach(department => {
            const option = document.createElement('option');
            option.value = department;
            option.textContent = department;
            departmentSelect.appendChild(option);
        });

        // Si hay un valor preseleccionado, cargar provincias
        if (departmentSelect.value) {
            loadProvinces(departmentSelect.value);
        }
    }
    
    // Cargar departamentos al iniciar la página
    if (departmentSelect) {
        loadDepartments();
    }

    // Función para cargar las provincias según el departamento seleccionado
    function loadProvinces(department) {
        if (!department) {
            clearSelect(provinceSelect, 'Seleccione un departamento primero');
            clearSelect(districtSelect, 'Seleccione una provincia primero');
            return;
        }

        // Si ya tenemos provincias en caché para este departamento, usarlas
        if (cache.provinces[department]) {
            populateProvinces(department, cache.provinces[department]);
            return;
        }

        // Mostrar estado de carga
        provinceSelect.innerHTML = '<option value="">Cargando...</option>';
        provinceSelect.disabled = true;
        clearSelect(districtSelect, 'Seleccione una provincia primero');

        const url = `${API_URLS.provinces}?department=${encodeURIComponent(department)}`;
        const fallbackUrl = `${API_URLS.alt_provinces}?department=${encodeURIComponent(department)}`;
        
        console.log('Solicitando provincias desde:', url);
        
        fetchWithFallback(url, fallbackUrl)
            .then(provinces => {
                console.log(`Provincias recibidas para ${department}:`, provinces);
                // Guardar en caché
                cache.provinces[department] = provinces;
                populateProvinces(department, provinces);
            })
            .catch(error => {
                console.error(`Error al cargar provincias para ${department}:`, error);
                provinceSelect.innerHTML = '<option value="">Error al cargar</option>';
                provinceSelect.disabled = true;
                clearSelect(districtSelect, 'Seleccione una provincia primero');
            });
    }

    // Función para poblar el selector de provincias
    function populateProvinces(department, provinces) {
        provinceSelect.innerHTML = '<option value="">Seleccione una provincia</option>';
        provinceSelect.disabled = false;

        provinces.forEach(province => {
            const option = document.createElement('option');
            option.value = province;
            option.textContent = province;
            provinceSelect.appendChild(option);
        });

        // Si hay un valor preseleccionado, cargar distritos
        if (provinceSelect.value) {
            loadDistricts(department, provinceSelect.value);
        }
    }

    // Evento para cuando cambia el departamento
    if (departmentSelect) {
        departmentSelect.addEventListener('change', function() {
            loadProvinces(this.value);
        });
    }

    // Función para cargar los distritos según la provincia seleccionada
    function loadDistricts(department, province) {
        if (!department || !province) {
            clearSelect(districtSelect, 'Seleccione una provincia primero');
            return;
        }

        // Clave para caché
        const cacheKey = `${department}-${province}`;

        // Si ya tenemos distritos en caché para esta combinación, usarlos
        if (cache.districts[cacheKey]) {
            populateDistricts(cache.districts[cacheKey]);
            return;
        }

        // Mostrar estado de carga
        districtSelect.innerHTML = '<option value="">Cargando...</option>';
        districtSelect.disabled = true;

        const url = `${API_URLS.districts}?department=${encodeURIComponent(department)}&province=${encodeURIComponent(province)}`;
        const fallbackUrl = `${API_URLS.alt_districts}?department=${encodeURIComponent(department)}&province=${encodeURIComponent(province)}`;
        
        console.log(`Solicitando distritos para departamento: ${department}, provincia: ${province}`);
        console.log('URL:', url);
        
        fetchWithFallback(url, fallbackUrl)
            .then(districts => {
                console.log(`Distritos recibidos para ${province}:`, districts);
                // Guardar en caché
                cache.districts[cacheKey] = districts;
                populateDistricts(districts);
            })
            .catch(error => {
                console.error(`Error al cargar distritos para ${province}:`, error);
                districtSelect.innerHTML = '<option value="">Error al cargar</option>';
                districtSelect.disabled = true;
            });
    }

    // Función para poblar el selector de distritos
    function populateDistricts(districts) {
        districtSelect.innerHTML = '<option value="">Seleccione un distrito</option>';
        districtSelect.disabled = false;

        districts.forEach(district => {
            const option = document.createElement('option');
            // Manejar tanto objetos con propiedad 'name' como strings directos
            const districtValue = typeof district === 'object' && district.name ? district.name : district;
            option.value = districtValue;
            option.textContent = districtValue;
            districtSelect.appendChild(option);
        });
    }

    // Evento para cuando cambia la provincia
    if (provinceSelect) {
        provinceSelect.addEventListener('change', function() {
            loadDistricts(departmentSelect.value, this.value);
        });
    }

    // Función para limpiar un selector y agregar una opción por defecto
    function clearSelect(selectElement, defaultText) {
        if (selectElement) {
            selectElement.innerHTML = '';
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = defaultText;
            selectElement.appendChild(defaultOption);
        }
    }
    
    // Función para intentar cargar datos con fallback automático
    function fetchWithFallback(url, fallbackUrl) {
        return new Promise((resolve, reject) => {
            // Intentar con la URL principal primero
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        console.warn(`Error en la respuesta principal: ${response.status} - ${response.statusText}`);
                        throw new Error(`Error ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Verificar si la respuesta es un array
                    if (!Array.isArray(data)) {
                        console.warn('La respuesta no es un array:', data);
                        data = [];
                    }
                    resolve(data);
                })
                .catch(error => {
                    console.warn(`Error con la URL principal (${url}):`, error);
                    console.log(`Intentando con URL alternativa: ${fallbackUrl}`);
                    
                    // Si falla, intentar con la URL alternativa
                    fetch(fallbackUrl)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`Error ${response.status}: ${response.statusText}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            // Verificar si la respuesta es un array
                            if (!Array.isArray(data)) {
                                console.warn('La respuesta alternativa no es un array:', data);
                                data = [];
                            }
                            resolve(data);
                        })
                        .catch(fallbackError => {
                            console.error('Error con ambas URLs:', fallbackError);
                            reject(fallbackError);
                        });
                });
        });
    }

    // Si ya hay un departamento seleccionado al cargar la página, cargar sus provincias
    if (departmentSelect && departmentSelect.value) {
        departmentSelect.dispatchEvent(new Event('change'));
        
        // Si ya hay una provincia seleccionada, cargar sus distritos
        if (provinceSelect && provinceSelect.value) {
            provinceSelect.dispatchEvent(new Event('change'));
        }
    }
});