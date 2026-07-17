"""
Ratio seguidores/no-seguidores y análisis de audiencia (Instagram y TikTok).

Instagram: Usa el campo 'alcance' (reach) vs 'visualizaciones' (impressions)
para estimar qué porcentaje del alcance viene de no-seguidores.

TikTok: Usa la ratio views/followers para estimar penetración fuera de la audiencia.
"""

import streamlit as st
import pandas as pd
from conexion import obtener_conexion


def _obtener_seguidores_actuales():
    """Obtiene el último conteo de seguidores por plataforma."""
    conexion = obtener_conexion()
    if not conexion:
        return {}
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT plataforma, seguidores 
            FROM seguidores_historico 
            WHERE (plataforma, fecha_registro) IN (
                SELECT plataforma, MAX(fecha_registro) 
                FROM seguidores_historico 
                GROUP BY plataforma
            )
        """)
        resultados = {row['plataforma']: row['seguidores'] for row in cursor.fetchall()}
        cursor.close()
        conexion.close()
        return resultados
    except Exception:
        conexion.close()
        return {}


def renderizar_ratio_audiencia(df):
    """Renderiza el análisis de ratio seguidores/no-seguidores (solo Instagram)."""

    st.markdown("#### 👥 Alcance: Seguidores vs Nuevas Audiencias")
    st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>¿Tu contenido llega a gente nueva o solo a los que ya te siguen?</p>", unsafe_allow_html=True)

    seguidores = _obtener_seguidores_actuales()

    # === SOLO INSTAGRAM ===
    st.markdown("**📸 Instagram**")
    df_ig = df[df['plataforma'] == 'instagram'].copy()
    seg_ig = seguidores.get('instagram', 0)

    if df_ig.empty or seg_ig == 0:
        st.caption("Sin datos suficientes.")
        return

    # Estimación: si vistas >> seguidores, estás alcanzando no-seguidores
    media_vistas = df_ig['visualizaciones'].mean()
    
    # Ratio de descubrimiento: vistas medias / seguidores
    ratio_descubrimiento = media_vistas / seg_ig * 100
    
    # Interpretación
    if ratio_descubrimiento > 100:
        pct_nuevos_est = min(int((ratio_descubrimiento - 100) / ratio_descubrimiento * 100), 90)
        color = "🟢"
        mensaje = "Tu contenido se muestra masivamente fuera de tus seguidores"
    elif ratio_descubrimiento > 50:
        pct_nuevos_est = int(ratio_descubrimiento * 0.4)
        color = "🟡"
        mensaje = "Buen equilibrio entre seguidores y audiencia nueva"
    else:
        pct_nuevos_est = max(int(ratio_descubrimiento * 0.3), 5)
        color = "🔴"
        mensaje = "Tu contenido llega mayormente a seguidores actuales"

    col_m, col_d = st.columns([1, 2])
    with col_m:
        st.metric(
            "Ratio descubrimiento",
            f"{ratio_descubrimiento:.0f}%",
            delta=f"~{pct_nuevos_est}% audiencia nueva"
        )
    with col_d:
        st.caption(f"{color} {mensaje}")

    # Desglose por formato
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Por formato:**")
    formatos_ig = df_ig.groupby('estilo_visual').agg(
        media_vistas=('visualizaciones', 'mean'),
        posts=('titulo', 'count')
    ).reset_index()
    formatos_ig['ratio_desc'] = (formatos_ig['media_vistas'] / seg_ig * 100).round(0)
    formatos_ig = formatos_ig[formatos_ig['posts'] >= 2].sort_values('ratio_desc', ascending=False)

    for _, row in formatos_ig.iterrows():
        icono = "🟢" if row['ratio_desc'] > 80 else ("🟡" if row['ratio_desc'] > 40 else "🔴")
        st.caption(f"{icono} {row['estilo_visual']}: {row['ratio_desc']:.0f}% ({int(row['posts'])} posts)")


def renderizar_ratio_audiencia_tiktok(df):
    """Renderiza el análisis de ratio seguidores/no-seguidores (solo TikTok)."""

    st.markdown("#### 👥 Alcance: Seguidores vs Nuevas Audiencias")
    st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>¿El algoritmo de TikTok te está mostrando a gente nueva?</p>", unsafe_allow_html=True)

    seguidores = _obtener_seguidores_actuales()

    st.markdown("**🎵 TikTok**")
    df_tt = df[df['plataforma'] == 'tiktok'].copy()
    seg_tt = seguidores.get('tiktok', 0)

    if df_tt.empty or seg_tt == 0:
        st.caption("Sin datos suficientes.")
        return

    media_vistas_tt = df_tt['visualizaciones'].mean()
    ratio_descubrimiento_tt = media_vistas_tt / seg_tt * 100

    if ratio_descubrimiento_tt > 200:
        pct_nuevos_tt = min(int((ratio_descubrimiento_tt - 100) / ratio_descubrimiento_tt * 100), 95)
        color_tt = "🟢"
        mensaje_tt = "El algoritmo te está empujando fuerte al FYP"
    elif ratio_descubrimiento_tt > 80:
        pct_nuevos_tt = int(ratio_descubrimiento_tt * 0.5)
        color_tt = "🟡"
        mensaje_tt = "Alcance decente fuera de seguidores"
    else:
        pct_nuevos_tt = max(int(ratio_descubrimiento_tt * 0.3), 5)
        color_tt = "🔴"
        mensaje_tt = "Tu contenido no está saliendo al FYP. Prueba otros formatos."

    col_m, col_d = st.columns([1, 2])
    with col_m:
        st.metric(
            "Ratio descubrimiento",
            f"{ratio_descubrimiento_tt:.0f}%",
            delta=f"~{pct_nuevos_tt}% audiencia nueva"
        )
    with col_d:
        st.caption(f"{color_tt} {mensaje_tt}")

    # Top posts por descubrimiento
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Posts que más te descubren:**")
    df_tt['ratio_post'] = (df_tt['visualizaciones'] / seg_tt * 100).round(0)
    top_desc = df_tt.sort_values('ratio_post', ascending=False).head(3)
    for _, row in top_desc.iterrows():
        st.caption(f"• {row['titulo'][:40]} → {row['ratio_post']:.0f}% de tus seguidores en vistas")
