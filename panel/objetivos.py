"""Módulo de objetivos y proyecciones de crecimiento."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from conexion import obtener_conexion


def cargar_objetivos():
    """Carga los objetivos activos desde la BD."""
    conexion = obtener_conexion()
    if not conexion:
        return pd.DataFrame()
    try:
        df = pd.read_sql("SELECT * FROM objetivos WHERE completado = FALSE ORDER BY fecha_objetivo", conexion)
        conexion.close()
        return df
    except Exception:
        conexion.close()
        return pd.DataFrame()


def guardar_objetivo(plataforma, metrica, valor_objetivo, fecha_objetivo):
    """Guarda un nuevo objetivo en la BD."""
    conexion = obtener_conexion()
    if not conexion:
        return False
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO objetivos (plataforma, metrica, valor_objetivo, fecha_inicio, fecha_objetivo)
            VALUES (%s, %s, %s, %s, %s)
        """, (plataforma, metrica, valor_objetivo, datetime.now().strftime('%Y-%m-%d'), fecha_objetivo))
        conexion.commit()
        cursor.close()
        conexion.close()
        return True
    except Exception:
        conexion.close()
        return False


def calcular_proyeccion(plataforma, df_seguidores):
    """Calcula la proyección de crecimiento basada en la tendencia reciente."""
    if df_seguidores.empty:
        return None, None

    df_plat = df_seguidores[df_seguidores['plataforma'] == plataforma].sort_values('fecha_registro')

    if len(df_plat) < 2:
        return None, None

    # Calcular crecimiento diario medio (últimos 14 días disponibles)
    df_reciente = df_plat.tail(14)
    primer_valor = int(df_reciente.iloc[0]['seguidores'])
    ultimo_valor = int(df_reciente.iloc[-1]['seguidores'])
    dias = (df_reciente.iloc[-1]['fecha_registro'] - df_reciente.iloc[0]['fecha_registro']).days

    if dias <= 0:
        return ultimo_valor, 0

    crecimiento_diario = (ultimo_valor - primer_valor) / dias
    return ultimo_valor, crecimiento_diario


def renderizar_objetivos(df_seguidores):
    """Renderiza la sección de objetivos en el panel."""
    st.markdown("### 🎯 Objetivos de Crecimiento")

    df_objetivos = cargar_objetivos()

    if df_objetivos.empty:
        st.caption("No hay objetivos definidos. Añade uno abajo.")
    else:
        for _, obj in df_objetivos.iterrows():
            plat = obj['plataforma']
            metrica = obj['metrica']
            objetivo = int(obj['valor_objetivo'])
            fecha_obj = pd.to_datetime(obj['fecha_objetivo'])

            emoji = {'instagram': '📸', 'tiktok': '🎵', 'youtube': '📺', 'global': '🌐'}.get(plat, '📊')

            if metrica == 'seguidores':
                actual, crecimiento_dia = calcular_proyeccion(plat, df_seguidores)

                if actual is not None:
                    progreso = min(actual / objetivo, 1.0) if objetivo > 0 else 0
                    faltan = max(objetivo - actual, 0)

                    # Proyección
                    if crecimiento_dia > 0:
                        dias_restantes = int(faltan / crecimiento_dia)
                        fecha_estimada = datetime.now() + timedelta(days=dias_restantes)
                        proyeccion_texto = f"A este ritmo (+{crecimiento_dia:.0f}/día) → llegas el **{fecha_estimada.strftime('%d/%m/%Y')}**"
                    elif crecimiento_dia == 0:
                        proyeccion_texto = "⚠️ Sin crecimiento detectado en los últimos días"
                    else:
                        proyeccion_texto = "📉 Estás perdiendo seguidores. Revisa la estrategia."

                    col_obj, col_prog = st.columns([2, 3])
                    with col_obj:
                        st.metric(
                            f"{emoji} {plat.capitalize()} — {metrica}",
                            f"{actual:,}".replace(',', '.'),
                            delta=f"Meta: {objetivo:,}".replace(',', '.')
                        )
                    with col_prog:
                        st.progress(progreso)
                        st.caption(proyeccion_texto)
                        dias_para_fecha = (fecha_obj - datetime.now()).days
                        if dias_para_fecha > 0:
                            st.caption(f"📅 Fecha límite: {fecha_obj.strftime('%d/%m/%Y')} ({dias_para_fecha} días)")
                        elif dias_para_fecha <= 0 and progreso < 1.0:
                            st.caption("⏰ ¡Fecha límite superada!")
                else:
                    st.caption(f"{emoji} {plat.capitalize()}: Sin datos de seguidores para proyectar")

    # Formulario para añadir objetivo
    with st.expander("➕ Añadir nuevo objetivo"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            nueva_plat = st.selectbox("Plataforma", ['instagram', 'tiktok', 'youtube'], key="obj_plat")
        with col2:
            nueva_metrica = st.selectbox("Métrica", ['seguidores'], key="obj_met")
        with col3:
            nuevo_valor = st.number_input("Meta", min_value=100, step=500, value=10000, key="obj_val")
        with col4:
            nueva_fecha = st.date_input("Fecha límite", value=datetime.now() + timedelta(days=90), key="obj_fecha")

        if st.button("💾 Guardar objetivo", key="btn_obj"):
            if guardar_objetivo(nueva_plat, nueva_metrica, nuevo_valor, nueva_fecha):
                st.success("✅ Objetivo guardado")
                st.rerun()
            else:
                st.error("Error al guardar")
