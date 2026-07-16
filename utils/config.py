"""
Módulo de configuración centralizada.
Lee y escribe tokens/credenciales desde la tabla `configuracion` de la BD.
Fallback a os.getenv() si la BD no está disponible.
"""

import os
from utils.logger import get_logger

logger = get_logger('config')

# Caché en memoria para no hacer queries repetidas en la misma ejecución
_cache = {}


def obtener_config(clave: str) -> str | None:
    """
    Lee un valor de configuración.
    Prioridad: caché memoria → BD (tabla configuracion) → os.getenv() → st.secrets
    """
    # 1. Caché en memoria
    if clave in _cache:
        return _cache[clave]
    
    # 2. Intentar leer de la BD
    try:
        from conexion import obtener_conexion
        con = obtener_conexion()
        if con:
            cursor = con.cursor()
            cursor.execute("SELECT valor FROM configuracion WHERE clave = %s", (clave,))
            resultado = cursor.fetchone()
            cursor.close()
            con.close()
            if resultado and resultado[0]:
                _cache[clave] = resultado[0]
                return resultado[0]
    except Exception:
        pass  # BD no disponible, seguimos con fallbacks
    
    # 3. Fallback: variable de entorno
    valor = os.getenv(clave)
    if valor:
        _cache[clave] = valor
        return valor
    
    # 4. Fallback: st.secrets (Streamlit Cloud)
    try:
        import streamlit as st
        valor = st.secrets[clave]
        if valor:
            _cache[clave] = valor
            return valor
    except Exception:
        pass
    
    return None


def guardar_config(clave: str, valor: str) -> bool:
    """
    Guarda/actualiza un valor en la tabla configuracion de la BD.
    Devuelve True si se guardó correctamente.
    """
    try:
        from conexion import obtener_conexion
        con = obtener_conexion()
        if con:
            cursor = con.cursor()
            cursor.execute("""
                INSERT INTO configuracion (clave, valor) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE valor = %s
            """, (clave, valor, valor))
            con.commit()
            cursor.close()
            con.close()
            # Actualizar caché
            _cache[clave] = valor
            logger.info(f"Config actualizada: {clave} = {valor[:15]}...")
            return True
    except Exception as e:
        logger.error(f"Error al guardar config '{clave}': {e}")
    return False


def limpiar_cache():
    """Limpia la caché en memoria (útil tras renovar tokens)."""
    _cache.clear()
