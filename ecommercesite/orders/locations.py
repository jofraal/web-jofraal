import json
import os
import logging
from functools import lru_cache

# Configurar logger
logger = logging.getLogger(__name__)

# Ruta al archivo JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.join(BASE_DIR, 'data', 'locations.json')

def load_locations():
    """
    Carga el archivo locations.json con los datos de departamentos, provincias y distritos.
    Retorna un diccionario con la estructura del archivo JSON.
    """
    logger.info(f"Intentando cargar: {JSON_FILE_PATH}")
    if not os.path.exists(JSON_FILE_PATH):
        logger.error(f"Archivo no encontrado en: {JSON_FILE_PATH}")
        raise FileNotFoundError(f"No se encontró el archivo en: {JSON_FILE_PATH}")
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Verificar que los datos tengan el formato esperado
            if not isinstance(data, dict):
                logger.error("Error: El archivo JSON no tiene el formato esperado. Se esperaba un diccionario.")
                return {}
            logger.info("Archivo de ubicaciones cargado correctamente")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {str(e)}")
        raise ValueError(f"Error al decodificar el archivo JSON en: {JSON_FILE_PATH} - {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al cargar el archivo JSON: {str(e)}")
        return {}

# Intentar cargar las ubicaciones al iniciar el módulo
# Si hay un error, volver a intentar con una ruta alternativa
try:
    PERU_LOCATIONS = load_locations()
    if not PERU_LOCATIONS:  # Si está vacío, intentar con una ruta alternativa
        logger.warning("Intentando cargar desde una ruta alternativa...")
        # Intentar con una ruta relativa al proyecto
        alt_path = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'orders', 'data', 'locations.json')
        if os.path.exists(alt_path):
            logger.info(f"Intentando cargar desde: {alt_path}")
            with open(alt_path, 'r', encoding='utf-8') as file:
                PERU_LOCATIONS = json.load(file)
                logger.info("Datos cargados correctamente desde ruta alternativa.")
        else:
            logger.error(f"No se encontró el archivo en la ruta alternativa: {alt_path}")
            PERU_LOCATIONS = {}
except (FileNotFoundError, ValueError) as e:
    logger.error(f"Error al cargar locations.json: {e}")
    PERU_LOCATIONS = {}

@lru_cache(maxsize=1)
def get_departments():
    """Obtiene la lista de departamentos con implementación de caché."""
    try:
        # Obtener los departamentos y eliminar espacios en blanco
        departments = [dept.strip() for dept in PERU_LOCATIONS.keys()]
        return departments
    except Exception as e:
        logger.error(f"Error al obtener departamentos: {e}")
        return []

@lru_cache(maxsize=32)
def get_provinces(department):
    """Obtiene las provincias para un departamento dado con implementación de caché."""
    try:
        if not department:
            logger.warning("Error: Departamento no especificado")
            return []
            
        # Eliminar espacios en blanco del nombre del departamento
        department = department.strip()
        
        # Buscar el departamento en el diccionario, considerando posibles espacios
        provinces = []
        for dept_key in PERU_LOCATIONS.keys():
            if dept_key.strip() == department:
                # Obtener las provincias y eliminar espacios en blanco
                provinces = [province.strip() for province in PERU_LOCATIONS[dept_key].keys()]
                break
        
        if not provinces:
            logger.warning(f"No se encontraron provincias para el departamento: {department}")
                
        return provinces
    except Exception as e:
        logger.error(f"Error al obtener provincias para {department}: {e}")
        return []

@lru_cache(maxsize=128)
def get_districts(department, province):
    """Obtiene los distritos para un departamento y provincia dados con implementación de caché."""
    try:
        if not department or not province:
            logger.warning("Error: Departamento o provincia no especificados")
            return []
        
        # Recortar espacios en blanco de los nombres
        department = department.strip()
        province = province.strip()
        
        # Buscar el departamento en el diccionario, considerando posibles espacios
        found_dept = None
        for dept_key in PERU_LOCATIONS.keys():
            if dept_key.strip() == department:
                found_dept = dept_key
                break
                
        if not found_dept:
            logger.warning(f"No se encontró el departamento: '{department}'")
            return []
            
        # Buscar la provincia en el diccionario, considerando posibles espacios
        districts = []
        for prov_key in PERU_LOCATIONS[found_dept].keys():
            if prov_key.strip() == province:
                districts = PERU_LOCATIONS[found_dept][prov_key]
                break
        
        if not districts:
            logger.warning(f"No se encontraron distritos para la provincia: '{province}' en el departamento: '{department}'")
        
        # Asegurarse de que districts sea una lista
        if not isinstance(districts, list):
            districts = list(districts) if districts else []
            
        # Recortar espacios en blanco de los nombres de los distritos
        districts = [district.strip() for district in districts]
        
        return districts
    except Exception as e:
        logger.error(f"Error al obtener distritos para {department}, {province}: {e}")
        return []