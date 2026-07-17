"""
Visualización del análisis de sentimiento en comentarios.
Muestra insights accionables sobre lo que la audiencia pide y siente.
"""

import json
import streamlit as st
import pandas as pd
from conexion import obtener_conexion


def _cargar_ultimo_analisis():
    """Carga el análisis de comentarios más reciente."""
    conexion = obtener_conexion()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM analisis_comentarios 
            WHERE plataforma = 'instagram'
            ORDER BY fecha_analisis DESC LIMIT 1
        """)
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        return resultado
    except Exception:
        conexion.close()
        return None


def _cargar_stats_comentarios():
    """Carga estadísticas básicas de los comentarios almacenados."""
    conexion = obtener_conexion()
    if not conexion:
        return 0, 0
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total, COUNT(DISTINCT id_contenido) as posts
            FROM comentarios_raw WHERE plataforma = 'instagram'
        """)
        row = cursor.fetchone()
        cursor.close()
        conexion.close()
        return row[0], row[1]
    except Exception:
        conexion.close()
        return 0, 0


def renderizar_sentimiento():
    """Renderiza la sección de análisis de sentimiento en el panel."""

    st.markdown("#### 💬 Lo que tu Audiencia Quiere")
    st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>Análisis de los comentarios reales de tus publicaciones.</p>", unsafe_allow_html=True)

    analisis = _cargar_ultimo_analisis()
    total_comentarios, total_posts = _cargar_stats_comentarios()

    if not analisis:
        st.caption(f"📝 {total_comentarios} comentarios almacenados de {total_posts} posts. El análisis se genera con el motor de IA (lunes y jueves).")
        return

    # Sentimiento global
    sentimiento = analisis.get('sentimiento_global', 'neutro')
    pct = analisis.get('pct_positivo', 0)

    emoji_sent = "🟢" if sentimiento == 'positivo' else ("🟡" if sentimiento == 'neutro' else "🔴")
    color_barra = "#4CAF50" if pct > 70 else ("#FFC107" if pct > 40 else "#F44336")

    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #E8E3DA; border-radius:10px; padding:1rem; margin-bottom:1rem;">
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
                <span style="font-size:0.7rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F;">Sentimiento general</span><br>
                <span style="font-size:1.3rem; font-family:Lora; color:#5C554B;">{emoji_sent} {pct}% positivo</span>
            </div>
            <div style="text-align:right;">
                <span style="font-size:0.7rem; color:#A39B8F;">{total_comentarios} comentarios analizados</span>
            </div>
        </div>
        <div style="background:#F4F1EA; border-radius:4px; height:6px; margin-top:8px; overflow:hidden;">
            <div style="background:{color_barra}; width:{pct}%; height:100%; border-radius:4px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tres columnas: Temas | Preguntas | Intenciones de compra
    col_temas, col_preg, col_compra = st.columns(3)

    # Temas de conversación
    with col_temas:
        st.markdown("**🔥 Temas que generan conversación**")
        temas_raw = analisis.get('temas_conversacion', '[]')
        try:
            temas = json.loads(temas_raw) if isinstance(temas_raw, str) else temas_raw
        except (json.JSONDecodeError, TypeError):
            temas = []

        if temas:
            for i, tema in enumerate(temas[:5], 1):
                st.caption(f"{i}. {tema}")
        else:
            st.caption("Sin datos aún.")

    # Preguntas frecuentes
    with col_preg:
        st.markdown("**❓ Tu audiencia pregunta**")
        preguntas_raw = analisis.get('preguntas_frecuentes', '[]')
        try:
            preguntas = json.loads(preguntas_raw) if isinstance(preguntas_raw, str) else preguntas_raw
        except (json.JSONDecodeError, TypeError):
            preguntas = []

        if preguntas:
            for preg in preguntas[:5]:
                st.caption(f"• {preg}")
        else:
            st.caption("Sin datos aún.")

    # Intenciones de compra
    with col_compra:
        st.markdown("**💰 Señales de compra**")
        compra_raw = analisis.get('intenciones_compra', '[]')
        try:
            compras = json.loads(compra_raw) if isinstance(compra_raw, str) else compra_raw
        except (json.JSONDecodeError, TypeError):
            compras = []

        if compras:
            for c in compras[:5]:
                st.caption(f"• \"{c}\"")
            st.markdown(f"<p style='font-size:0.7rem; color:#5C554B; margin-top:8px;'><strong>{len(compras)}</strong> señal(es) detectada(s)</p>", unsafe_allow_html=True)
        else:
            st.caption("Sin señales de compra detectadas.")

    # Resumen de la IA
    resumen = analisis.get('resumen_ia', '')
    if resumen:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#F4F1EA; border:1px solid #E8E3DA; border-radius:8px; padding:1rem;">
            <p style="font-size:0.7rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F; margin:0 0 6px;">💡 Recomendación de la IA</p>
            <p style="font-size:0.82rem; color:#4A453F; line-height:1.6; margin:0;">{resumen}</p>
        </div>
        """, unsafe_allow_html=True)

    # Fecha del análisis
    fecha = analisis.get('fecha_analisis')
    if fecha:
        fecha_str = pd.to_datetime(fecha).strftime('%d/%m/%Y %H:%M')
        st.caption(f"📅 Último análisis: {fecha_str}")
