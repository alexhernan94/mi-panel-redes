"""Módulo de carga de datos desde la base de datos."""

import pandas as pd
import streamlit as st
from conexion import obtener_conexion


@st.cache_data(ttl=3600)
def cargar_datos_panel():
    """Carga métricas y datos de IA desde la BD con caché de 1 hora."""
    conexion = obtener_conexion()
    if conexion:
        query_metricas = """
            SELECT c.plataforma, c.estilo_visual, c.titulo, c.fecha_publicacion, c.url,
                   MAX(m.visualizaciones) as visualizaciones, MAX(m.likes) as likes,
                   MAX(m.compartidos) as compartidos, MAX(m.guardados) as guardados
            FROM contenidos c
            JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
            GROUP BY c.id_contenido, c.plataforma, c.estilo_visual, c.titulo, c.fecha_publicacion, c.url
        """
        df_m = pd.read_sql(query_metricas, conexion)
        query_ia = "SELECT tendencias_actuales, analisis_rendimiento, ideas_contenido, fecha_generacion FROM insights_ia ORDER BY id_insight DESC LIMIT 10"
        df_i = pd.read_sql(query_ia, conexion)
        conexion.close()
        return df_m, df_i
    return pd.DataFrame(), pd.DataFrame()
