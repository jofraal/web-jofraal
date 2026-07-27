/**
 * Configuración y validación de variables de entorno para la aplicación
 * Este archivo centraliza la gestión de variables de entorno del lado del cliente
 */

// Objeto global para gestionar la configuración de variables de entorno
const EnvConfig = (function() {
    // Variables de entorno requeridas para el funcionamiento de la aplicación
    const required = {
        MERCADOPAGO_PUBLIC_KEY: typeof MERCADOPAGO_PUBLIC_KEY !== 'undefined' ? MERCADOPAGO_PUBLIC_KEY : null
    };
    
    // Variables de entorno opcionales (la aplicación puede funcionar sin ellas)
    const optional = {
        GOOGLE_MAPS_API_KEY: typeof GOOGLE_MAPS_API_KEY !== 'undefined' ? GOOGLE_MAPS_API_KEY : null
    };
    
    /**
     * Valida todas las variables de entorno requeridas
     * @returns {Object} Resultado de la validación
     */
    function validateRequired() {
        const missingVars = [];
        
        for (const [key, value] of Object.entries(required)) {
            if (!value) {
                missingVars.push(key);
                console.error(`Error: La variable de entorno ${key} no está definida o está vacía`);
            }
        }
        
        return {
            isValid: missingVars.length === 0,
            missingVars: missingVars
        };
    }
    
    /**
     * Valida variables opcionales y muestra advertencias
     * @returns {Object} Resultado de la validación
     */
    function validateOptional() {
        const missingVars = [];
        
        for (const [key, value] of Object.entries(optional)) {
            if (!value) {
                missingVars.push(key);
                console.warn(`Advertencia: La variable de entorno opcional ${key} no está definida`);
            }
        }
        
        return {
            missingVars: missingVars
        };
    }
    
    /**
     * Valida todas las variables de entorno (requeridas y opcionales)
     * @returns {Object} Resultado completo de la validación
     */
    function validateAll() {
        const required = validateRequired();
        const optional = validateOptional();
        
        return {
            isValid: required.isValid,
            missingRequired: required.missingVars,
            missingOptional: optional.missingVars
        };
    }
    
    /**
     * Obtiene el valor de una variable de entorno
     * @param {string} key - Nombre de la variable
     * @returns {string|null} Valor de la variable o null si no existe
     */
    function get(key) {
        if (required.hasOwnProperty(key)) {
            return required[key];
        }
        
        if (optional.hasOwnProperty(key)) {
            return optional[key];
        }
        
        console.warn(`Advertencia: Se intentó acceder a una variable de entorno no definida: ${key}`);
        return null;
    }
    
    // API pública
    return {
        validateRequired,
        validateOptional,
        validateAll,
        get
    };
})();

// Ejecutar validación al cargar el script
document.addEventListener('DOMContentLoaded', function() {
    const validation = EnvConfig.validateAll();
    
    if (!validation.isValid) {
        console.error('Error: Faltan variables de entorno requeridas:', validation.missingRequired.join(', '));
    }
    
    if (validation.missingOptional.length > 0) {
        console.warn('Advertencia: Faltan variables de entorno opcionales:', validation.missingOptional.join(', '));
    }
});