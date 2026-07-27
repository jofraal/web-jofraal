// users/js/location_selectors_fixed.js
document.addEventListener('DOMContentLoaded', function() {
    // Obtener referencias a los selectores
    const departmentSelect = document.getElementById('department');
    const provinceSelect = document.getElementById('province');
    const districtSelect = document.getElementById('district');
    
    // Verificar que existan los selectores en el DOM
    if (!departmentSelect || !provinceSelect || !districtSelect) {
        console.error('No se encontraron los selectores de ubicación');
        return;
    }

    // Caché para almacenar datos y evitar solicitudes repetidas
    const cache = {
        departments: [],
        provinces: {},
        districts: {}
    };

    // URLs de API con sistema de fallback
    const API_URLS = {
        // URLs principales (users)
        departments: '/users/api/get-departments/',
        provinces: '/users/api/get-provinces/',
        districts: '/users/api/get-districts/',
        // URLs alternativas (orders)
        alt_departments: '/orders/api/departments/',
        alt_provinces: '/orders/api/provinces/',
        alt_districts: '/orders/api/districts/'
    };

    // Función para intentar cargar datos con fallback
    async function fetchWithFallback(primaryUrl, fallbackUrl) {
        try {
            console.log('Intentando cargar desde:', primaryUrl);
            const response = await fetch(primaryUrl);
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            console.log('Datos recibidos:', data);
            return data;
        } catch (error) {
            console.warn(`Error al cargar desde ${primaryUrl}:`, error.message);
            console.log('Intentando cargar desde fallback:', fallbackUrl);
            try {
                const fallbackResponse = await fetch(fallbackUrl);
                if (!fallbackResponse.ok) {
                    throw new Error(`Error en fallback ${fallbackResponse.status}: ${fallbackResponse.statusText}`);
                }
                const fallbackData = await fallbackResponse.json();
                console.log('Datos recibidos (fallback):', fallbackData);
                return fallbackData;
            } catch (fallbackError) {
                console.error('Error en fallback:', fallbackError.message);
                throw new Error(`No se pudieron cargar los datos desde ninguna fuente: ${fallbackError.message}`);
            }
        }
    }

    // Función para resetear un selector
    function resetSelect(select, message) {
        select.innerHTML = `<option value="">${message}</option>`;
        select.disabled = true;
    }

    // Normalizar datos para manejar ambos formatos: ["..."] o [{name: "..."}]
    function normalizeData(data) {
        if (!Array.isArray(data)) {
            console.warn('La respuesta no es un array:', data);
            return [];
        }
        return data.map(item => {
            if (typeof item === 'string') {
                return { name: item };
            } else if (item && typeof item === 'object' && 'name' in item) {
                return item;
            } else {
                console.warn('Formato de dato no reconocido:', item);
                return null;
            }
        }).filter(item => item !== null);
    }

    // Cargar departamentos
    function loadDepartments() {
        if (cache.departments.length > 0) {
            populateDepartments(cache.departments);
            return;
        }
        resetSelect(departmentSelect, 'Cargando departamentos...');
        resetSelect(provinceSelect, 'Seleccione un departamento primero');
        resetSelect(districtSelect, 'Seleccione una provincia primero');
        fetchWithFallback(API_URLS.departments, API_URLS.alt_departments)
            .then(departments => {
                console.log(`Departamentos recibidos: ${departments.length}`, departments);
                const normalizedDepartments = normalizeData(departments);
                cache.departments = normalizedDepartments;
                populateDepartments(normalizedDepartments);
            })
            .catch(error => {
                console.error('Error al cargar departamentos:', error.message);
                resetSelect(departmentSelect, 'Error al cargar departamentos');
            });
    }

    // Poblar el selector de departamentos
    function populateDepartments(departments) {
        departmentSelect.innerHTML = '<option value="">Seleccione un departamento</option>';
        departmentSelect.disabled = false;
        departments.forEach(department => {
            const option = document.createElement('option');
            option.value = department.name;
            option.textContent = department.name;
            departmentSelect.appendChild(option);
        });
        if (departmentSelect.value) {
            loadProvinces(departmentSelect.value);
        }
    }

    // Cargar provincias para un departamento
    function loadProvinces(department) {
        if (!department) {
            resetSelect(provinceSelect, 'Seleccione un departamento primero');
            resetSelect(districtSelect, 'Seleccione una provincia primero');
            return;
        }
        if (cache.provinces[department]) {
            populateProvinces(department, cache.provinces[department]);
            return;
        }
        resetSelect(provinceSelect, 'Cargando provincias...');
        resetSelect(districtSelect, 'Seleccione una provincia primero');
        const primaryUrl = `${API_URLS.provinces}?department=${encodeURIComponent(department)}`;
        const fallbackUrl = `${API_URLS.alt_provinces}?department=${encodeURIComponent(department)}`;
        fetchWithFallback(primaryUrl, fallbackUrl)
            .then(provinces => {
                console.log(`Provincias recibidas para ${department}: ${provinces.length}`, provinces);
                const normalizedProvinces = normalizeData(provinces);
                cache.provinces[department] = normalizedProvinces;
                populateProvinces(department, normalizedProvinces);
            })
            .catch(error => {
                console.error(`Error al cargar provincias para ${department}:`, error.message);
                resetSelect(provinceSelect, 'Error al cargar provincias');
            });
    }

    // Poblar el selector de provincias
    function populateProvinces(department, provinces) {
        provinceSelect.innerHTML = '<option value="">Seleccione una provincia</option>';
        provinceSelect.disabled = false;
        provinces.forEach(province => {
            const option = document.createElement('option');
            option.value = province.name;
            option.textContent = province.name;
            provinceSelect.appendChild(option);
        });
        if (provinceSelect.value) {
            loadDistricts(department, provinceSelect.value);
        }
    }

    // Cargar distritos para una provincia
    function loadDistricts(department, province) {
        if (!department || !province) {
            resetSelect(districtSelect, 'Seleccione una provincia primero');
            return;
        }
        const cacheKey = `${department}-${province}`;
        if (cache.districts[cacheKey]) {
            populateDistricts(cache.districts[cacheKey]);
            return;
        }
        resetSelect(districtSelect, 'Cargando distritos...');
        const primaryUrl = `${API_URLS.districts}?department=${encodeURIComponent(department)}&province=${encodeURIComponent(province)}`;
        const fallbackUrl = `${API_URLS.alt_districts}?department=${encodeURIComponent(department)}&province=${encodeURIComponent(province)}`;
        fetchWithFallback(primaryUrl, fallbackUrl)
            .then(districts => {
                console.log(`Distritos recibidos para ${province}: ${districts.length}`, districts);
                const normalizedDistricts = normalizeData(districts);
                cache.districts[cacheKey] = normalizedDistricts;
                populateDistricts(normalizedDistricts);
            })
            .catch(error => {
                console.error(`Error al cargar distritos para ${province}:`, error.message);
                resetSelect(districtSelect, 'Error al cargar distritos');
            });
    }

    // Poblar el selector de distritos
    function populateDistricts(districts) {
        districtSelect.innerHTML = '<option value="">Seleccione un distrito</option>';
        districtSelect.disabled = false;
        districts.forEach(district => {
            const option = document.createElement('option');
            option.value = district.name;
            option.textContent = district.name;
            districtSelect.appendChild(option);
        });
    }

    // Iniciar carga de departamentos
    loadDepartments();

    // Configurar eventos de cambio
    departmentSelect.addEventListener('change', function() {
        loadProvinces(this.value);
    });

    provinceSelect.addEventListener('change', function() {
        loadDistricts(departmentSelect.value, this.value);
    });

    // Si hay valores preseleccionados, disparar los eventos de cambio
    if (departmentSelect.value) {
        departmentSelect.dispatchEvent(new Event('change'));
    }
});