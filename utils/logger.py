"""
Sistema de logging estructurado.
Escribe en consola Y en archivo logs/panel.log.
"""

import logging
import os
from datetime import datetime

# Crear directorio de logs si no existe
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, 'panel.log')


def get_logger(nombre: str) -> logging.Logger:
    """
    Devuelve un logger configurado con salida a consola y archivo.
    
    Uso:
        from utils import get_logger
        logger = get_logger(__name__)
        logger.info("Extrayendo datos de Instagram...")
        logger.error("Fallo al conectar")
    """
    logger = logging.getLogger(nombre)
    
    # Evitar duplicar handlers si se llama varias veces
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Formato: [2026-07-16 10:30:45] [instagram] INFO - Extrayendo datos...
    formato = logging.Formatter(
        '[%(asctime)s] [%(name)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler consola
    handler_consola = logging.StreamHandler()
    handler_consola.setLevel(logging.INFO)
    handler_consola.setFormatter(formato)
    logger.addHandler(handler_consola)
    
    # Handler archivo (rotación manual por tamaño)
    try:
        handler_archivo = logging.FileHandler(LOG_FILE, encoding='utf-8')
        handler_archivo.setLevel(logging.DEBUG)
        handler_archivo.setFormatter(formato)
        logger.addHandler(handler_archivo)
    except Exception:
        pass  # En Streamlit Cloud no hay acceso a escribir archivos
    
    return logger
