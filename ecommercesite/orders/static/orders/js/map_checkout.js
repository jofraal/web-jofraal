// ecommercesite\orders\static\orders\js\map_checkout.js
(function() {
    // Encerrar todo el código en una IIFE para evitar conflictos globales
    let map;
    let geocoder;
    let locationConfirmed = false;
    let mapVisible = false;
    let apiLoaded = false;
    let apiError = false;
    let marker; // Declarar marker explícitamente en el ámbito local

    // Función para manejar errores de carga de la API
    function handleApiError() {
        apiError = true;
        const mapContainer = document.getElementById('map-container');
        const errorMsg = document.createElement('div');
        errorMsg.className = 'p-4 mb-4 text-sm text-red-700 bg-red-100 rounded-md';
        errorMsg.innerHTML = '<strong>Error:</strong> No se pudo cargar el mapa de Google. El error "REQUEST_DENIED" indica que la clave API no es válida o no está configurada correctamente. Por favor, contacte al administrador del sitio.';
        mapContainer.prepend(errorMsg);

        const confirmButton = document.getElementById('confirm-location');
        if (confirmButton) {
            confirmButton.disabled = true;
            confirmButton.classList.add('opacity-50', 'cursor-not-allowed');
            confirmButton.classList.remove('hover:bg-green-700');
        }
    }

    // Hacer la función initMap accesible globalmente
    window.initMap = function() {
        apiLoaded = true;
        let lat, lng;
        try {
            geocoder = new google.maps.Geocoder();
            lat = parseFloat(document.getElementById('latitude').value) || -12.046374;
            lng = parseFloat(document.getElementById('longitude').value) || -77.042793;
            const initialPosition = { lat, lng };
            console.log('Inicializando mapa con coordenadas:', lat, lng);

            map = new google.maps.Map(document.getElementById('map'), {
                center: initialPosition,
                zoom: 15,
                mapTypeControl: true,
                streetViewControl: false
            });

            marker = new google.maps.Marker({
                position: initialPosition,
                map: map,
                draggable: true,
                animation: google.maps.Animation.DROP,
                title: 'Arrastra para ajustar la ubicación'
            });

            // Actualizar coordenadas cuando se arrastra el marcador
            google.maps.event.addListener(marker, 'dragend', function() {
                const position = marker.getPosition();
                document.getElementById('latitude').value = position.lat();
                document.getElementById('longitude').value = position.lng();
                updateAddressFromCoordinates(position.lat(), position.lng());
            });

            // Permitir hacer clic en el mapa para mover el marcador
            google.maps.event.addListener(map, 'click', function(event) {
                marker.setPosition(event.latLng);
                document.getElementById('latitude').value = event.latLng.lat();
                document.getElementById('longitude').value = event.latLng.lng();
                updateAddressFromCoordinates(event.latLng.lat(), event.latLng.lng());
            });

            // Buscar ubicación basada en la dirección cuando cambian los campos
            document.getElementById('id_street').addEventListener('change', updateMapFromAddress);
            document.getElementById('id_district').addEventListener('change', updateMapFromAddress);

            if (lat && lng && lat !== -12.046374 && lng !== -77.042793) {
                updateAddressFromCoordinates(lat, lng);
            }
        } catch (error) {
            console.error('Error al inicializar el mapa:', error);
            handleApiError();
        }
    };

    function updateMapFromAddress() {
        const street = document.getElementById('id_street').value;
        const streetNumber = document.getElementById('id_street_number').value;
        const district = document.getElementById('id_district').value;
        const province = document.getElementById('id_province').value;
        const department = document.getElementById('id_department').value;
        const addressDisplay = document.getElementById('address-display');

        if (!geocoder || apiError) {
            if (addressDisplay) {
                addressDisplay.textContent = 'No se puede buscar la dirección: Error en la API de Google Maps';
                addressDisplay.classList.remove('hidden');
            }
            return;
        }

        if (street && district) {
            const address = `${street} ${streetNumber}, ${district}, ${province}, ${department}, Perú`;
            console.log('Buscando dirección:', address);

            try {
                geocoder.geocode({ 'address': address }, function(results, status) {
                    if (status === 'OK' && results[0]) {
                        const location = results[0].geometry.location;
                        console.log('Coordenadas encontradas:', location.lat(), location.lng());
                        map.setCenter(location);
                        marker.setPosition(location);
                        document.getElementById('latitude').value = location.lat();
                        document.getElementById('longitude').value = location.lng();
                        updateAddressFromCoordinates(location.lat(), location.lng());
                    } else {
                        let errorMsg = 'Error al buscar la dirección: ';
                        if (status === 'REQUEST_DENIED') {
                            errorMsg += 'La solicitud fue denegada. Verifique que la clave API sea válida.';
                        } else if (status === 'ZERO_RESULTS') {
                            errorMsg += 'No se encontraron resultados para esta dirección.';
                        } else if (status === 'OVER_QUERY_LIMIT') {
                            errorMsg += 'Se ha excedido el límite de consultas diarias.';
                        } else if (status === 'INVALID_REQUEST') {
                            errorMsg += 'La solicitud es inválida.';
                        } else {
                            errorMsg += status;
                        }
                        if (addressDisplay) {
                            addressDisplay.textContent = errorMsg;
                            addressDisplay.classList.remove('hidden');
                        }
                        console.error(errorMsg);
                    }
                });
            } catch (error) {
                console.error('Error al geocodificar la dirección:', error);
                if (addressDisplay) {
                    addressDisplay.textContent = 'Error al procesar la dirección: ' + error.message;
                    addressDisplay.classList.remove('hidden');
                }
            }
        }
    }

    function updateAddressFromCoordinates(lat, lng) {
        const latlng = { lat: parseFloat(lat), lng: parseFloat(lng) };
        const addressDisplay = document.getElementById('address-display');

        if (!addressDisplay) {
            console.error('Elemento address-display no encontrado');
            return;
        }

        console.log('Actualizando dirección desde coordenadas:', lat, lng);

        if (!geocoder || apiError) {
            addressDisplay.textContent = 'No se puede obtener la dirección: Error en la API de Google Maps';
            addressDisplay.classList.remove('hidden');
            return;
        }

        geocoder.geocode({ 'location': latlng }, function(results, status) {
            if (status === 'OK') {
                if (results[0]) {
                    const formattedAddress = results[0].formatted_address;
                    console.log('Dirección encontrada:', formattedAddress);
                    addressDisplay.textContent = 'Dirección: ' + formattedAddress;
                    addressDisplay.classList.remove('hidden');

                    const mapContainer = document.getElementById('map-container');
                    if (mapContainer && mapContainer.classList.contains('hidden')) {
                        const confirmButton = document.getElementById('confirm-location');
                        if (confirmButton) {
                            confirmButton.click();
                        }
                    }
                } else {
                    addressDisplay.textContent = 'No se encontró ninguna dirección para esta ubicación';
                    addressDisplay.classList.remove('hidden');
                }
            } else {
                let errorMsg = 'Error al obtener la dirección: ';
                if (status === 'REQUEST_DENIED') {
                    errorMsg += 'La solicitud fue denegada. Verifique que la clave API sea válida y esté habilitada para Geocoding API.';
                } else if (status === 'OVER_QUERY_LIMIT') {
                    errorMsg += 'Se ha excedido el límite de consultas diarias.';
                } else if (status === 'INVALID_REQUEST') {
                    errorMsg += 'La solicitud es inválida.';
                } else {
                    errorMsg += status;
                }
                addressDisplay.textContent = errorMsg;
                addressDisplay.classList.remove('hidden');
                console.error(errorMsg);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        const confirmButton = document.getElementById('confirm-location');
        const mapContainer = document.getElementById('map-container');
        const shippingForm = document.getElementById('shipping-form');

        if (shippingForm) {
            shippingForm.addEventListener('submit', function() {
                const latField = document.getElementById('latitude');
                const lngField = document.getElementById('longitude');
                console.log('Enviando formulario con coordenadas:', latField.value, lngField.value);

                if (!shippingForm.querySelector('input[name="latitude"]')) {
                    const hiddenLatField = document.createElement('input');
                    hiddenLatField.type = 'hidden';
                    hiddenLatField.name = 'latitude';
                    hiddenLatField.value = latField.value;
                    shippingForm.appendChild(hiddenLatField);
                }

                if (!shippingForm.querySelector('input[name="longitude"]')) {
                    const hiddenLngField = document.createElement('input');
                    hiddenLngField.type = 'hidden';
                    hiddenLngField.name = 'longitude';
                    hiddenLngField.value = lngField.value;
                    shippingForm.appendChild(hiddenLngField);
                }
            });
        }

        if (confirmButton) {
            confirmButton.addEventListener('click', function() {
                if (!mapVisible) {
                    mapContainer.classList.remove('hidden');
                    mapVisible = true;
                    this.textContent = 'Ocultar mapa';

                    if (apiError) {
                        return;
                    }

                    setTimeout(function() {
                        if (map && google && google.maps && google.maps.event) {
                            try {
                                google.maps.event.trigger(map, 'resize');
                                const lat = parseFloat(document.getElementById('latitude').value);
                                const lng = parseFloat(document.getElementById('longitude').value);
                                if (lat && lng) {
                                    map.setCenter({ lat, lng });
                                }
                            } catch (error) {
                                console.error('Error al redimensionar el mapa:', error);
                            }
                        }
                    }, 100);
                } else {
                    mapContainer.classList.add('hidden');
                    mapVisible = false;
                    this.textContent = 'Ubicación en el mapa';
                }
            });
        }

        if (marker && google && google.maps) {
            google.maps.event.addListener(marker, 'dragend', function() {
                locationConfirmed = true;
                console.log('Ubicación confirmada por arrastre del marcador');
            });

            google.maps.event.addListener(map, 'click', function() {
                locationConfirmed = true;
                console.log('Ubicación confirmada por clic en el mapa');
            });
        }
    });

    // Manejo del botón mostrar-mapa-btn (si existe)
    const mostrarMapaBtn = document.getElementById('mostrar-mapa-btn');
    if (mostrarMapaBtn) {
        mostrarMapaBtn.addEventListener('click', function() {
            const mapContainer = document.getElementById('map-container');
            if (mapContainer) {
                mapContainer.classList.remove('hidden');
            }
            if (typeof cargarGoogleMapsUnaVez === 'function') {
                cargarGoogleMapsUnaVez();
            } else if (typeof initMap === 'function' && !(window.google && window.google.maps)) {
                if (!document.querySelector('script[src*="maps.googleapis.com/maps/api/js"]')) {
                    const script = document.createElement('script');
                    script.src = 'https://maps.googleapis.com/maps/api/js?key=' + (window.GOOGLE_MAPS_API_KEY || '') + '&callback=initMap&libraries=marker&loading=async';
                    script.async = true;
                    script.onerror = handleApiError;
                    document.head.appendChild(script);
                }
            }
        });
    }

    // Hacer funciones accesibles globalmente
    window.updateMapFromAddress = updateMapFromAddress;
    window.updateAddressFromCoordinates = updateAddressFromCoordinates;
})();