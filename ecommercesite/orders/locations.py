import logging
from functools import lru_cache
from core.locations import PERU_LOCATIONS, get_departments, get_provinces, get_districts

# Configurar logger
logger = logging.getLogger(__name__)
