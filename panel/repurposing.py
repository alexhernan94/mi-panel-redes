"""
Auto-repurposing sugerido.

Detecta contenido que funcionó bien en una plataforma y sugiere adaptarlo a la otra.
Prioridad: IG → TT (60% peso IG) y TT → IG (30% peso TT).
"""

import streamlit as st
import pandas as pd


def _calcular_score_viral(row):
    """Score de viralidad para determinar qué contenido vale la pena repurposear."""
    return (
        row.get('compartidos', 0) * 5 +
        row.get('guardados', 0) * 4 +
        row.get('likes', 0) * 1 +
        row.get('visualizaciones', 0) * 0.01
    )


def _sugerir_adaptacion(formato_origen, plataforma_destino):
    """Sugiere cómo adaptar el contenido al nuevo formato."""
    adaptaciones = {
        ('Reel', 'tiktok'): {
            'formato_destino': 'Vídeo vertical',
            'tip': 'Publica sin cambios (mismo ratio). Cambia la música por un trending sound de TT. Añade texto en pantalla los primeros 2s.',
        },
        ('Carrusel', 'tiktok'): {
            'formato_destino': 'Vídeo vertical (slideshow)',
            'tip': 'Convierte las slides en un vídeo con transiciones suaves (2s por slide). Añade una voz en off o música ASMR.',
        },
        ('Post Foto', 'tiktok'): {
            'formato_destino': 'Vídeo vertical (reveal)',
            'tip': 'Graba el proceso de creación de la obra como time-lapse o "art reveal" con audio satisfactorio.',
        },
        ('Story', 'tiktok'): {
            'formato_destino': 'Vídeo vertical',
            'tip': 'Compila las stories del día en un mini-vlog vertical para TikTok.',
        },
        ('Vídeo vertical', 'instagram'): {
            'formato_destino': 'Reel',
            'tip': 'Publica directamente como Reel. Adapta el caption a IG (más largo, con hashtags del nicho arte). Añade ubicación.',
        },
    }

    key = (formato_origen, plataforma_destino)
    if key in adaptaciones:
        return adaptaciones[key]

    # Default
    if plataforma_destino == 'tiktok':
        return {'formato_destino': 'Vídeo vertical', 'tip': 'Adapta el contenido a formato vertical con hook en el primer segundo.'}
    else:
        return {'formato_destino': 'Reel', 'tip': 'Publica como Reel con caption optimizado y hashtags del nicho.'}


def renderizar_repurposing(df):
    """Renderiza sugerencias de auto-repurposing de Instagram a TikTok."""

    st.markdown("#### 🔄 Contenido para Reciclar (IG → TikTok)")
    st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>Posts que funcionaron bien en Instagram y deberías adaptar a TikTok.</p>", unsafe_allow_html=True)

    if df.empty:
        st.caption("Sin datos suficientes.")
        return

    df_ig = df[df['plataforma'] == 'instagram'].copy()
    if df_ig.empty:
        st.caption("Sin datos de Instagram.")
        return

    df_ig['score_viral'] = df_ig.apply(_calcular_score_viral, axis=1)
    media_ig = df_ig['score_viral'].mean()

    # IG → TikTok: top posts de IG que se pueden adaptar
    df_ig_top = df_ig[
        (df_ig['score_viral'] > media_ig) &
        (df_ig['estilo_visual'].isin(['Reel', 'Carrusel', 'Post Foto', 'Story']))
    ].sort_values('score_viral', ascending=False).head(5)

    if df_ig_top.empty:
        st.caption("No hay contenido de IG que destaque lo suficiente para repurposear.")
    else:
        for _, row in df_ig_top.iterrows():
            adaptacion = _sugerir_adaptacion(row['estilo_visual'], 'tiktok')
            st.markdown(f"""
            <div style="background:#F4F1EA; border:1px solid #E8E3DA; border-radius:8px; padding:12px; margin-bottom:8px;">
                <p style="margin:0; font-size:0.82rem; color:#5C554B; font-weight:500;">{row['titulo'][:60]}</p>
                <p style="margin:4px 0 0; font-size:0.72rem; color:#A39B8F;">
                    📸 {row['estilo_visual']} → 🎵 <strong>{adaptacion['formato_destino']}</strong><br>
                    💡 {adaptacion['tip']}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("💡 Repurposear no es repostear sin cambios. Adapta el gancho, la música y el caption a TikTok.")


def renderizar_repurposing_tiktok(df):
    """Renderiza sugerencias de auto-repurposing de TikTok a Instagram."""

    st.markdown("#### 🔄 Contenido para Reciclar (TikTok → IG)")
    st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>Vídeos que funcionaron bien en TikTok y deberías adaptar a Instagram.</p>", unsafe_allow_html=True)

    if df.empty:
        st.caption("Sin datos suficientes.")
        return

    df_tt = df[df['plataforma'] == 'tiktok'].copy()
    if df_tt.empty:
        st.caption("Sin datos de TikTok.")
        return

    df_tt['score_viral'] = df_tt.apply(_calcular_score_viral, axis=1)
    media_tt = df_tt['score_viral'].mean()

    df_tt_top = df_tt[df_tt['score_viral'] > media_tt].sort_values('score_viral', ascending=False).head(5)

    if df_tt_top.empty:
        st.caption("No hay contenido de TikTok que destaque lo suficiente para repurposear.")
    else:
        for _, row in df_tt_top.iterrows():
            adaptacion = _sugerir_adaptacion(row['estilo_visual'], 'instagram')
            st.markdown(f"""
            <div style="background:#F4F1EA; border:1px solid #E8E3DA; border-radius:8px; padding:12px; margin-bottom:8px;">
                <p style="margin:0; font-size:0.82rem; color:#5C554B; font-weight:500;">{row['titulo'][:60]}</p>
                <p style="margin:4px 0 0; font-size:0.72rem; color:#A39B8F;">
                    🎵 Vídeo vertical → 📸 <strong>{adaptacion['formato_destino']}</strong><br>
                    💡 {adaptacion['tip']}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("💡 Repurposear no es repostear sin cambios. Adapta el caption, la música y los hashtags a Instagram.")
