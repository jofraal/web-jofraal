/**
 * Script optimizado para generar un menú desplegable de ubicaciones en checkout.html
 * Utiliza los mismos endpoints API que location_selectors.js para mantener consistencia
 */
document.addEventListener('DOMContentLoaded', function() {
    const menuContainer = document.getElementById('locations-menu');
    if (!menuContainer) {
        console.error('No se encontró el contenedor del menú de ubicaciones');
        return;
    }

    // Variable para almacenar en caché los datos de ubicaciones
    let locationsData = {};
    
    // Cargar departamentos usando el mismo endpoint API que location_selectors.js
    fetch("/orders/api/departments/")
        .then(response => {
            if (!response.ok) {
                throw new Error('No se pudo cargar los departamentos');
            }
            return response.json();
        })
        .then(departments => {
            // Iterar sobre cada departamento
            departments.forEach(department => {
                const li = document.createElement('li');
                li.className = 'relative';
                li.setAttribute('x-data', '{ open: false }');
                li.setAttribute('@mouseenter', 'open = true');
                li.setAttribute('@mouseleave', 'open = false');

                const span = document.createElement('span');
                span.className = 'block px-4 py-2 text-sm text-gray-800 cursor-pointer hover:bg-gray-100';
                span.textContent = department;
                li.appendChild(span);

                // Crear submenú para provincias
                const provincesSubmenu = document.createElement('ul');
                provincesSubmenu.className = 'absolute top-0 left-full bg-white border border-gray-300 rounded-md shadow-lg min-w-[200px] z-10';
                provincesSubmenu.setAttribute('x-show', 'open');
                provincesSubmenu.setAttribute('x-transition', '');
                
                // Cargar provincias solo cuando se pasa el mouse sobre el departamento (lazy loading)
                li.addEventListener('mouseenter', function() {
                    // Si ya tenemos las provincias en caché, no hacer otra petición
                    if (locationsData[department]) {
                        renderProvinces(department, locationsData[department], provincesSubmenu);
                        return;
                    }
                    
                    // Cargar provincias usando el endpoint API
                    fetch(`/orders/api/provinces/?department=${encodeURIComponent(department)}`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`No se pudo cargar las provincias de ${department}`);
                            }
                            return response.json();
                        })
                        .then(provinces => {
                            // Guardar en caché
                            locationsData[department] = provinces;
                            renderProvinces(department, provinces, provincesSubmenu);
                        })
                        .catch(error => {
                            console.error(`Error al cargar provincias de ${department}:`, error);
                            provincesSubmenu.innerHTML = '<li class="px-4 py-2 text-sm text-red-500">Error al cargar provincias</li>';
                        });
                }, { once: true }); // Solo ejecutar una vez
                menuContainer.appendChild(li);
            });
            
            // Función para renderizar provincias
            function renderProvinces(department, provinces, provincesSubmenu) {
                // Limpiar el contenido previo
                provincesSubmenu.innerHTML = '';
                
                // Iterar sobre cada provincia
                provinces.forEach(province => {
                    const provinceLi = document.createElement('li');
                    provinceLi.className = 'relative';
                    provinceLi.setAttribute('x-data', '{ open: false }');
                    provinceLi.setAttribute('@mouseenter', 'open = true');
                    provinceLi.setAttribute('@mouseleave', 'open = false');

                    const provinceSpan = document.createElement('span');
                    provinceSpan.className = 'block px-4 py-2 text-sm text-gray-800 cursor-pointer hover:bg-gray-100';
                    provinceSpan.textContent = province;
                    provinceLi.appendChild(provinceSpan);

                    // Crear submenú para distritos
                    const districtsSubmenu = document.createElement('ul');
                    districtsSubmenu.className = 'absolute top-0 left-full bg-white border border-gray-300 rounded-md shadow-lg min-w-[200px] z-10';
                    districtsSubmenu.setAttribute('x-show', 'open');
                    districtsSubmenu.setAttribute('x-transition', '');
                    
                    // Cargar distritos solo cuando se pasa el mouse sobre la provincia (lazy loading)
                    provinceLi.addEventListener('mouseenter', function() {
                        // Cargar distritos usando el endpoint API
                        fetch(`/orders/api/districts/?department=${encodeURIComponent(department)}&province=${encodeURIComponent(province)}`)
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error(`No se pudo cargar los distritos de ${province}`);
                                }
                                return response.json();
                            })
                            .then(districts => {
                                // Limpiar el contenido previo
                                districtsSubmenu.innerHTML = '';
                                
                                // Renderizar distritos
                                districts.forEach(district => {
                                    const districtLi = document.createElement('li');
                                    const districtA = document.createElement('a');
                                    districtA.className = 'block px-4 py-2 text-sm text-gray-800 hover:bg-gray-100';
                                    districtA.textContent = district;
                                    districtA.href = '#';
                                    
                                    // Actualizar selectores al hacer clic
                                    districtA.addEventListener('click', function(e) {
                                        e.preventDefault();
                                        updateLocationSelectors(department, province, district);
                                    });
                                    
                                    districtLi.appendChild(districtA);
                                    districtsSubmenu.appendChild(districtLi);
                                });
                            })
                            .catch(error => {
                                console.error(`Error al cargar distritos de ${province}:`, error);
                                districtsSubmenu.innerHTML = '<li class="px-4 py-2 text-sm text-red-500">Error al cargar distritos</li>';
                            });
                    }, { once: true }); // Solo ejecutar una vez

                    provinceLi.appendChild(districtsSubmenu);
                    provincesSubmenu.appendChild(provinceLi);
                });
            }
        })
        .catch(error => {
            console.error('Error al cargar departamentos:', error);
            menuContainer.innerHTML = '<li class="px-4 py-2 text-sm text-red-500">Error al cargar ubicaciones</li>';
        });
        
    // Función para actualizar los selectores de ubicación
    function updateLocationSelectors(department, province, district) {
        const departmentSelect = document.getElementById('id_department');
        const provinceSelect = document.getElementById('id_province');
        const districtSelect = document.getElementById('id_district');

        if (departmentSelect && provinceSelect && districtSelect) {
            // Actualizar departamento y disparar evento change
            departmentSelect.value = department;
            departmentSelect.dispatchEvent(new Event('change'));
            
            // Esperar a que se carguen las provincias
            const checkProvinceOptions = setInterval(() => {
                if (provinceSelect.options.length > 1) {
                    clearInterval(checkProvinceOptions);
                    
                    // Actualizar provincia y disparar evento change
                    provinceSelect.value = province;
                    provinceSelect.dispatchEvent(new Event('change'));
                    
                    // Esperar a que se carguen los distritos
                    const checkDistrictOptions = setInterval(() => {
                        if (districtSelect.options.length > 1) {
                            clearInterval(checkDistrictOptions);
                            
                            // Actualizar distrito
                            districtSelect.value = district;
                            districtSelect.dispatchEvent(new Event('change'));
                        }
                    }, 50);
                }
            }, 50);
        }
    }
});