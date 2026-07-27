// location_selectors.js

document.addEventListener('DOMContentLoaded', function () {
    const departmentSelect = document.getElementById('id_department');
    const provinceSelect = document.getElementById('id_province');
    const districtSelect = document.getElementById('id_district');

    if (!departmentSelect || !provinceSelect || !districtSelect) {
        console.error('No se encontraron los elementos de ubicación');
        return;
    }
    
    // Cargar departamentos al iniciar
    fetch('/orders/api/departments/')
        .then(response => response.json())
        .then(data => {
            departmentSelect.innerHTML = '<option value="">Seleccione un departamento</option>';
            data.forEach(department => {
                const option = new Option(department, department);
                departmentSelect.add(option);
            });
        })
        .catch(error => {
            console.error('Error al cargar departamentos:', error);
            departmentSelect.innerHTML = '<option value="">Error al cargar</option>';
        });

    // Cargar provincias cuando cambia el departamento
    departmentSelect.addEventListener('change', function () {
        const department = this.value;
        if (!department) {
            provinceSelect.innerHTML = '<option value="">Seleccione una provincia</option>';
            districtSelect.innerHTML = '<option value="">Seleccione un distrito</option>';
            return;
        }

        fetch(`/orders/api/provinces/?department=${encodeURIComponent(department)}`)
            .then(response => response.json())
            .then(data => {
                provinceSelect.innerHTML = '<option value="">Seleccione una provincia</option>';
                data.forEach(province => {
                    const option = new Option(province, province);
                    provinceSelect.add(option);
                });
            })
            .catch(error => {
                console.error('Error al cargar provincias:', error);
                provinceSelect.innerHTML = '<option value="">Error al cargar</option>';
            });
    });

    // Cargar distritos cuando cambia la provincia
    provinceSelect.addEventListener('change', function () {
        const province = this.value;
        const department = departmentSelect.value;

        if (!province || !department) {
            districtSelect.innerHTML = '<option value="">Seleccione un distrito</option>';
            return;
        }

        fetch(`/orders/api/districts/?department=${encodeURIComponent(department)}&province=${encodeURIComponent(province)}`)
            .then(response => response.json())
            .then(data => {
                districtSelect.innerHTML = '<option value="">Seleccione un distrito</option>';
                data.forEach(district => {
                    const option = new Option(district, district);
                    districtSelect.add(option);
                });
            })
            .catch(error => {
                console.error('Error al cargar distritos:', error);
                districtSelect.innerHTML = '<option value="">Error al cargar</option>';
            });
    });

    // Cargar valores iniciales si existen
    if (departmentSelect.value) {
        departmentSelect.dispatchEvent(new Event('change'));
        setTimeout(() => {
            if (provinceSelect.value) {
                provinceSelect.dispatchEvent(new Event('change'));
            }
        }, 500);
    }
});