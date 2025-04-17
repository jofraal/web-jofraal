/**
 * Script optimizado para manejar los selectores de ubicación en cascada (departamento, provincia, distrito)
 * Usa vistas API para obtener datos dinámicamente con implementación de caché
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
        districts: {}
    };

    // Función para mostrar mensajes de error en los selectores
    function showError(select, message) {
        select.innerHTML = `<option value="">${message}</option>`;
        select.disabled = true;
        select.classList.add('border-red-300');
    }

    // Función para restablecer un selector
    function resetSelect(select, defaultText = '') {
        select.innerHTML = `<option value="">${defaultText}</option>`;
        select.disabled = true;
        select.classList.remove('border-red-300');
    }

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
            })
            .catch(error => {
                console.error('Error al cargar departamentos:', error);
                showError(departmentSelect, 'Error al cargar');
                resetSelect(provinceSelect, 'Seleccione un departamento primero');
                resetSelect(districtSelect, 'Seleccione una provincia primero');
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

    // Función para cargar las provincias según el departamento seleccionado
    function loadProvinces(department) {
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

        // Mostrar estado de carga
        provinceSelect.innerHTML = '<option value="">Cargando...</option>';
        provinceSelect.disabled = true;
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
            })
            .catch(error => {
                console.error(`Error al cargar provincias para ${department}:`, error);
                showError(provinceSelect, 'Error al cargar');
                resetSelect(districtSelect, 'Seleccione una provincia primero');
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

    // Función para cargar los distritos según la provincia seleccionada
    function loadDistricts(department, province) {
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

        // Mostrar estado de carga
        districtSelect.innerHTML = '<option value="">Cargando...</option>';
        districtSelect.disabled = true;

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
            })
            .catch(error => {
                console.error(`Error al cargar distritos para ${province}:`, error);
                showError(districtSelect, 'Error al cargar');
            });
    }

    // Función para poblar el selector de distritos
    function populateDistricts(districts) {
        districtSelect.innerHTML = '<option value="">Seleccione un distrito</option>';
        districtSelect.disabled = false;

        districts.forEach(district => {
            const option = document.createElement('option');
            option.value = district;
            option.textContent = district;
            districtSelect.appendChild(option);
        });
    }

    // Cargar departamentos al iniciar
    loadDepartments();

    // Evento para cuando cambia el departamento
    departmentSelect.addEventListener('change', function() {
        console.log('Departamento cambiado a:', this.value);
        loadProvinces(this.value);
    });

    // Evento para cuando cambia la provincia
    provinceSelect.addEventListener('change', function() {
        console.log('Provincia cambiada a:', this.value);
        loadDistricts(departmentSelect.value, this.value);
    });
});