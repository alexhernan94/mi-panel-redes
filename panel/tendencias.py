"""
Detector de tendencias del nicho (diferenciado IG vs TikTok).

Analiza los hashtags y títulos del contenido propio para detectar:
1. Qué temas/formatos están creciendo en engagement
2. Qué hashtags del nicho arte/slow living están funcionando
3. Diferencias de tendencias entre IG y TT
"""

import re
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter


# Hashtags del nicho para monitorizar (arte, ilustración, slow living, handmade)
HASHTAGS_NICHO = {
    'instagram': [
        'arttok', 'artprocess', 'watercolorart', 'handmadepaper', 'slowliving',
        'artistlife', 'creativeliving', 'artjournal', 'illustrationart', 'papermaking',
        'sustainableart', 'artesanal', 'hechoamano', 'acuarela', 'ilustracion',
        'procesoartistico', 'vidaslow', 'arteslow', 'arteconsciente', 'papelreciclado'
    ],
    'tiktok': [
        'arttok', 'artprocess', 'watercolortok', 'asmrart', 'satisfying',
        'handmade', 'smallbusiness', 'artistcheck', 'sketchbook', 'drawtok',
        'cottagecore', 'slowliving', 'procesocreativo', 'arteadictos', 'dibujo',
        'pintura', 'papelartesanal', 'hechoamano', 'timelapse', 'artreels'
    ]
}


def _extraer_hashtags(df):
    """Extrae todos los hashtags usados con sus métricas."""
    hashtags_data = []
    for _, row in df.iterrows():
        tags = re.findall(r'#(\w+)', str(row['titulo']).lower())
        for tag in tags:
            if len(tag) > 3:
                hashtags_data.append({
                    'hashtag': tag,
                    'plataforma': row['plataforma'],
                    'vistas': row['visualizaciones'],
                    'likes': row['likes'],
                    'compartidos': row.get('compartidos', 0),
                    'guardados': row.get('guardados', 0),
                    'fecha': row['fecha_publicacion']
                })
    return pd.DataFrame(hashtags_data)


def _detectar_tendencias_emergentes(df_hashtags, plataforma, dias_recientes=14):
    """Detecta hashtags cuyo rendimiento está subiendo."""
    if df_hashtags.empty:
        return []

    df_plat = df_hashtags[df_hashtags['plataforma'] == plataforma].copy()
    if df_plat.empty:
        return []

    ahora = datetime.now()
    fecha_corte = ahora - timedelta(days=dias_recientes)

    # Agrupar por hashtag: rendimiento reciente vs histórico
    tendencias = []
    for tag in df_plat['hashtag'].unique():
        df_tag = df_plat[df_plat['hashtag'] == tag]
        if len(df_tag) < 2:
            continue

        recientes = df_tag[df_tag['fecha'] >= fecha_corte]
        antiguos = df_tag[df_tag['fecha'] < fecha_corte]

        if recientes.empty or antiguos.empty:
            continue

        media_reciente = recientes['vistas'].mean()
        media_antigua = antiguos['vistas'].mean()

        if media_antigua > 0:
            crecimiento = (media_reciente - media_antigua) / media_antigua * 100
            tendencias.append({
                'hashtag': f"#{tag}",
                'crecimiento': round(crecimiento, 0),
                'media_vistas_reciente': int(media_reciente),
                'usos_recientes': len(recientes),
                'usos_total': len(df_tag)
            })

    # Ordenar por crecimiento
    tendencias.sort(key=lambda x: x['crecimiento'], reverse=True)
    return tendencias


def _detectar_formatos_creciendo(df, plataforma, dias_recientes=14):
    """Detecta qué formatos están mejorando en rendimiento."""
    df_plat = df[df['plataforma'] == plataforma].copy()
    if len(df_plat) < 5:
        return []

    ahora = datetime.now()
    fecha_corte = ahora - timedelta(days=dias_recientes)

    resultados = []
    for formato in df_plat['estilo_visual'].unique():
        df_fmt = df_plat[df_plat['estilo_visual'] == formato]
        recientes = df_fmt[df_fmt['fecha_publicacion'] >= fecha_corte]
        antiguos = df_fmt[df_fmt['fecha_publicacion'] < fecha_corte]

        if recientes.empty or antiguos.empty or len(recientes) < 2:
            continue

        eng_reciente = (recientes['likes'] / recientes['visualizaciones'].replace(0, 1) * 100).mean()
        eng_antiguo = (antiguos['likes'] / antiguos['visualizaciones'].replace(0, 1) * 100).mean()

        if eng_antiguo > 0:
            cambio = eng_reciente - eng_antiguo
            resultados.append({
                'formato': formato,
                'engagement_reciente': round(eng_reciente, 2),
                'cambio': round(cambio, 2),
                'posts_recientes': len(recientes)
            })

    resultados.sort(key=lambda x: x['cambio'], reverse=True)
    return resultados


def renderizar_tendencias(df):
    """Renderiza el detector de tendencias solo para Instagram."""

    st.markdown("#### 📈 Tendencias del Nicho (Instagram)")
    st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>Qué está creciendo en tu nicho (arte, slow living, handmade) en Instagram.</p>", unsafe_allow_html=True)

    if df.empty:
        st.caption("Sin datos suficientes.")
        return

    df_ig = df[df['plataforma'] == 'instagram'].copy()
    if df_ig.empty:
        st.caption("Sin datos de Instagram.")
        return

    df_hashtags = _extraer_hashtags(df_ig)

    # Formatos creciendo
    formatos_ig = _detectar_formatos_creciendo(df_ig, 'instagram')
    if formatos_ig:
        st.markdown("**Formatos en alza:**")
        for fmt in formatos_ig[:3]:
            flecha = "📈" if fmt['cambio'] > 0 else "📉"
            st.caption(f"{flecha} **{fmt['formato']}**: {fmt['engagement_reciente']}% eng ({fmt['cambio']:+.1f}%)")
    
    # Hashtags del nicho que mejor funcionan
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Hashtags del nicho que funcionan:**")
    
    if not df_hashtags.empty:
        nicho_ig = df_hashtags[df_hashtags['hashtag'].isin(HASHTAGS_NICHO['instagram'])]
        if not nicho_ig.empty:
            rendimiento_nicho = nicho_ig.groupby('hashtag').agg(
                media_vistas=('vistas', 'mean'),
                usos=('vistas', 'count')
            ).sort_values('media_vistas', ascending=False).head(5)
            
            for tag, row in rendimiento_nicho.iterrows():
                st.caption(f"#{tag} → {int(row['media_vistas']):,} vistas/post ({int(row['usos'])} usos)")
        else:
            st.caption("Prueba usar hashtags del nicho: #artprocess #slowliving #watercolorart #papelreciclado")

    # Tendencias emergentes
    tendencias_ig = _detectar_tendencias_emergentes(df_hashtags, 'instagram')
    if tendencias_ig:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Hashtags que están creciendo:**")
        for t in tendencias_ig[:3]:
            if t['crecimiento'] > 0:
                st.caption(f"🔥 {t['hashtag']}: +{t['crecimiento']:.0f}% vistas últimos 14 días")


def renderizar_diferencias_plataformas(df):
    """Renderiza la comparativa entre plataformas (para pestaña General)."""
    
    st.markdown("### 🔑 Diferencias Clave entre Plataformas")
    
    df_ig_stats = df[df['plataforma'] == 'instagram']
    df_tt_stats = df[df['plataforma'] == 'tiktok']
    
    if df_ig_stats.empty or df_tt_stats.empty:
        st.caption("Se necesitan datos de ambas plataformas para comparar.")
        return

    eng_ig = (df_ig_stats['likes'] / df_ig_stats['visualizaciones'].replace(0, 1) * 100).mean()
    eng_tt = (df_tt_stats['likes'] / df_tt_stats['visualizaciones'].replace(0, 1) * 100).mean()
    vistas_ig = df_ig_stats['visualizaciones'].mean()
    vistas_tt = df_tt_stats['visualizaciones'].mean()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📸 Instagram", f"{eng_ig:.1f}% eng", delta=f"{vistas_ig:,.0f} vistas/post")
    with col2:
        st.metric("🎵 TikTok", f"{eng_tt:.1f}% eng", delta=f"{vistas_tt:,.0f} vistas/post")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if vistas_tt > vistas_ig * 2:
        st.info("💡 **TikTok te da más alcance bruto.** Úsalo para descubrimiento. Instagram es mejor para convertir (guardados, tráfico a web, ventas).")
    elif eng_ig > eng_tt:
        st.info("💡 **Instagram te da más engagement real.** Tu audiencia de IG actúa más. Usa TikTok para atraer gente nueva e Instagram para fidelizar y vender.")
    else:
        st.info("💡 Ambas plataformas rinden similar. Prioriza Instagram (60%) por su capacidad de conversión y cercanía con la audiencia.")


def renderizar_tendencias_tiktok(df):
    """Renderiza el detector de tendencias solo para TikTok."""

    st.markdown("#### 📈 Tendencias del Nicho (TikTok)")
    st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>Qué está creciendo en tu nicho (arte, ASMR, slow living) en TikTok.</p>", unsafe_allow_html=True)

    if df.empty:
        st.caption("Sin datos suficientes.")
        return

    df_tt = df[df['plataforma'] == 'tiktok'].copy()
    if df_tt.empty:
        st.caption("Sin datos de TikTok.")
        return

    df_hashtags = _extraer_hashtags(df_tt)

    # Formatos creciendo
    formatos_tt = _detectar_formatos_creciendo(df_tt, 'tiktok')
    if formatos_tt:
        st.markdown("**Formatos en alza:**")
        for fmt in formatos_tt[:3]:
            flecha = "📈" if fmt['cambio'] > 0 else "📉"
            st.caption(f"{flecha} **{fmt['formato']}**: {fmt['engagement_reciente']}% eng ({fmt['cambio']:+.1f}%)")

    # Hashtags del nicho
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Hashtags del nicho que funcionan:**")

    if not df_hashtags.empty:
        nicho_tt = df_hashtags[df_hashtags['hashtag'].isin(HASHTAGS_NICHO['tiktok'])]
        if not nicho_tt.empty:
            rendimiento_nicho_tt = nicho_tt.groupby('hashtag').agg(
                media_vistas=('vistas', 'mean'),
                usos=('vistas', 'count')
            ).sort_values('media_vistas', ascending=False).head(5)

            for tag, row in rendimiento_nicho_tt.iterrows():
                st.caption(f"#{tag} → {int(row['media_vistas']):,} vistas/post ({int(row['usos'])} usos)")
        else:
            st.caption("Prueba: #arttok #asmrart #satisfying #watercolortok #procesocreativo")

    # Tendencias emergentes
    tendencias_tt = _detectar_tendencias_emergentes(df_hashtags, 'tiktok')
    if tendencias_tt:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Hashtags que están creciendo:**")
        for t in tendencias_tt[:3]:
            if t['crecimiento'] > 0:
                st.caption(f"🔥 {t['hashtag']}: +{t['crecimiento']:.0f}% vistas últimos 14 días")
