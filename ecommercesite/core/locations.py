import json
import os
import logging
from functools import lru_cache
from pathlib import Path

# Configurar logger
logger = logging.getLogger(__name__)

# Rutas de búsqueda para el archivo locations.json
LOCATIONS_PATHS = [
    Path(__file__).parent.parent / "data" / "locations.json",
    Path(__file__).parent.parent / "static" / "data" / "locations.json",
    Path(__file__).parent.parent / "orders" / "data" / "locations.json",
    Path(__file__).parent.parent / "users" / "data" / "locations.json",
]

@lru_cache(maxsize=1)
def load_locations():
    """Carga centralizada del archivo locations.json."""
    for path in LOCATIONS_PATHS:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    if not isinstance(data, dict):
                        logger.error(f"El archivo JSON en {path} no es un diccionario.")
                        continue
                    if not data:
                        logger.warning(f"El archivo JSON en {path} está vacío.")
                        continue
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar JSON en {path}: {str(e)}")
            except Exception as e:
                logger.error(f"Error inesperado al cargar {path}: {str(e)}")
    
    logger.error("No se pudo cargar locations.json desde ninguna ruta.")
    return {}

# Cargar ubicaciones al iniciar el módulo
PERU_LOCATIONS = load_locations()

@lru_cache(maxsize=1)
def get_departments():
    """Obtiene la lista de departamentos."""
    try:
        return [dept.strip() for dept in PERU_LOCATIONS.keys()]
    except Exception as e:
        logger.error(f"Error al obtener departamentos: {e}")
        return []

@lru_cache(maxsize=32)
def get_provinces(department):
    """Obtiene las provincias para un departamento."""
    try:
        if not department:
            logger.warning("Departamento no especificado.")
            return []
        
        department = department.strip()
        provinces = []
        for dept_key in PERU_LOCATIONS.keys():
            if dept_key.strip() == department:
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
    """Obtiene los distritos para un departamento y provincia."""
    try:
        if not department or not province:
            logger.warning("Departamento o provincia no especificados.")
            return []
        
        department = department.strip()
        province = province.strip()
        found_dept = None
        
        for dept_key in PERU_LOCATIONS.keys():
            if dept_key.strip() == department:
                found_dept = dept_key
                break
        
        if not found_dept:
            logger.warning(f"No se encontró el departamento: '{department}'")
            return []
        
        districts = []
        for prov_key in PERU_LOCATIONS[found_dept].keys():
            if prov_key.strip() == province:
                districts = [district.strip() for district in PERU_LOCATIONS[found_dept][prov_key]]
                break
        
        if not districts:
            logger.warning(f"No se encontraron distritos para la provincia: '{province}' en el departamento: '{department}'")
        
        return districts
    except Exception as e:
        logger.error(f"Error al obtener distritos para {department}, {province}: {e}")
        return []