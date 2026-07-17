"""
Módulo "Qué publicar hoy" — Vista accionable diaria.

Prioridad de plataformas:
- Instagram: 60%
- TikTok: 30%
- YouTube: 10%
"""

import re
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ_MADRID = ZoneInfo("Europe/Madrid")

# Pesos de plataforma (determinan la frecuencia de aparición en el calendario)
PESOS_PLATAFORMA = {
    'instagram': 0.60,
    'tiktok': 0.30,
    'youtube': 0.10,
}

# Mapping día → plataforma principal (basado en pesos: IG 4 días, TT 2 días, YT 1 día)
CALENDARIO_PLATAFORMA = {
    0: 'instagram',   # Lunes
    1: 'tiktok',      # Martes
    2: 'instagram',   # Miércoles
    3: 'tiktok',      # Jueves
    4: 'instagram',   # Viernes
    5: 'instagram',   # Sábado
    6: 'youtube',     # Domingo
}

# Formatos recomendados por plataforma y día (basado en patrones de engagement típicos)
FORMATOS_DIA = {
    0: {'plataforma': 'instagram', 'formato': 'Reel', 'emoji': '🎬', 'razon': 'Los lunes el alcance de Reels es alto (gente en transporte/descanso)'},
    1: {'plataforma': 'tiktok', 'formato': 'Vídeo vertical', 'emoji': '🎵', 'razon': 'Martes es buen día para TikTok (engagement estable entre semana)'},
    2: {'plataforma': 'instagram', 'formato': 'Carrusel', 'emoji': '🖼️', 'razon': 'Los carruseles funcionan a mitad de semana (tiempo de lectura en pausas)'},
    3: {'plataforma': 'tiktok', 'formato': 'Vídeo vertical', 'emoji': '🎵', 'razon': 'Jueves prepara el terreno para el fin de semana en TikTok'},
    4: {'plataforma': 'instagram', 'formato': 'Reel', 'emoji': '🎬', 'razon': 'Viernes alta actividad en IG (gente relajándose)'},
    5: {'plataforma': 'instagram', 'formato': 'Story', 'emoji': '🤳', 'razon': 'Sábado es día de stories (contenido casual, behind the scenes)'},
    6: {'plataforma': 'youtube', 'formato': 'Vídeo largo', 'emoji': '📺', 'razon': 'Domingo = watch time largo (la gente tiene tiempo para vídeos completos)'},
}


def _obtener_mejor_hora(df_metricas, plataforma):
    """Calcula la mejor hora para publicar hoy en la plataforma dada."""
    df_plat = df_metricas[df_metricas['plataforma'] == plataforma].copy()

    if len(df_plat) < 3:
        # Defaults razonables
        defaults = {'instagram': 19, 'tiktok': 20, 'youtube': 17}
        return defaults.get(plataforma, 18)

    try:
        df_plat['hora'] = df_plat['fecha_publicacion'].dt.tz_localize('UTC').dt.tz_convert(TZ_MADRID).dt.hour
    except Exception:
        df_plat['hora'] = df_plat['fecha_publicacion'].dt.hour

    df_plat['engagement_pct'] = (df_plat['likes'] / df_plat['visualizaciones'].replace(0, 1) * 100)
    eng_hora = df_plat.groupby('hora')['engagement_pct'].mean()

    if eng_hora.empty:
        return 19

    return int(eng_hora.idxmax())


def _obtener_idea_hoy(ideas_plataforma, formato):
    """Extrae la primera idea relevante para el formato del día."""
    if not ideas_plataforma or ideas_plataforma == "Generando ideas...":
        return None

    # Buscar por formato
    formato_tags = {
        'Reel': '[REEL]',
        'Carrusel': '[CARRUSEL]',
        'Story': '[STORY]',
        'Vídeo vertical': '[TIKTOK VERTICAL]',
        'Vídeo largo': '[VIDEO LARGO]',
        'Short': '[SHORT]',
    }

    tag = formato_tags.get(formato, '')
    if tag and tag in ideas_plataforma:
        # Extraer el bloque de esa idea
        partes = ideas_plataforma.split(tag)
        if len(partes) > 1:
            # Tomar desde el tag hasta el siguiente tag o fin
            bloque = partes[1]
            # Cortar en el siguiente tag de formato
            for otro_tag in formato_tags.values():
                if otro_tag in bloque:
                    bloque = bloque.split(otro_tag)[0]
                    break
            return f"{tag} {bloque.strip()}"

    # Si no hay match exacto, devolver la primera idea disponible
    lineas = ideas_plataforma.split('\n')
    primeras = [l.strip() for l in lineas if l.strip() and not l.strip().startswith('-')]
    return primeras[0] if primeras else None


def _obtener_caption_hoy(captions_ia, plataforma):
    """Extrae un caption relevante para la plataforma del día."""
    if not captions_ia:
        return None

    plat_upper = plataforma.upper()
    lineas = captions_ia.split('\n')
    caption_actual = ""
    caption_encontrado = ""

    for linea in lineas:
        linea_s = linea.strip()
        if not linea_s:
            continue
        if linea_s[0].isdigit() and '.' in linea_s[:3]:
            if caption_actual and plat_upper in caption_actual.upper():
                caption_encontrado = caption_actual.strip()
                break
            caption_actual = linea_s.split('.', 1)[1].strip() + "\n"
        else:
            caption_actual += linea_s + "\n"

    if not caption_encontrado and caption_actual and plat_upper in caption_actual.upper():
        caption_encontrado = caption_actual.strip()

    # Si no hay uno específico para esta plataforma, devolver el primero
    if not caption_encontrado:
        todos = captions_ia.split('\n')
        bloque = ""
        for l in todos:
            l = l.strip()
            if l and l[0].isdigit() and '.' in l[:3]:
                if bloque:
                    return bloque.strip()
                bloque = l.split('.', 1)[1].strip() + "\n"
            elif bloque:
                bloque += l + "\n"
        if bloque:
            return bloque.strip()

    return caption_encontrado or None


def _dias_sin_publicar(df_metricas, plataforma):
    """Calcula cuántos días lleva sin publicar en una plataforma."""
    df_plat = df_metricas[df_metricas['plataforma'] == plataforma]
    if df_plat.empty:
        return 99
    ultima = df_plat['fecha_publicacion'].max()
    return (datetime.now() - ultima).days


def renderizar_hoy(df_metricas, ideas_ig, ideas_tt, ideas_yt, captions_ia, planificador_semanal):
    """Renderiza la vista 'Qué publicar hoy'."""

    ahora = datetime.now(TZ_MADRID)
    dia_semana = ahora.weekday()  # 0=lunes, 6=domingo
    dia_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][dia_semana]

    config_hoy = FORMATOS_DIA[dia_semana]
    plataforma = config_hoy['plataforma']
    formato = config_hoy['formato']
    emoji_formato = config_hoy['emoji']
    razon = config_hoy['razon']

    emoji_plat = {'instagram': '📸', 'tiktok': '🎵', 'youtube': '📺'}[plataforma]

    # Mejor hora
    mejor_hora = _obtener_mejor_hora(df_metricas, plataforma)

    # Header del día
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #F4F1EA 0%, #FDFBF7 100%); border: 1px solid #E8E3DA; border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem;">
        <p style="font-family: Montserrat; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2px; color: #A39B8F; margin: 0;">Hoy es {dia_nombre}</p>
        <h2 style="font-family: Lora; color: #5C554B; margin: 0.5rem 0; font-size: 1.8rem;">{emoji_formato} Publica un {formato} en {emoji_plat} {plataforma.capitalize()}</h2>
        <p style="font-family: Montserrat; font-size: 1.1rem; color: #7B7163; margin: 0;">Hora óptima: <strong>{mejor_hora:02d}:00</strong> (Madrid)</p>
    </div>
    """, unsafe_allow_html=True)

    # Tres columnas: Idea | Caption | Estado
    col_idea, col_caption, col_estado = st.columns([2, 2, 1], gap="large")

    with col_idea:
        st.markdown("#### 💡 Idea de contenido")
        ideas_map = {'instagram': ideas_ig, 'tiktok': ideas_tt, 'youtube': ideas_yt}
        idea = _obtener_idea_hoy(ideas_map.get(plataforma, ''), formato)
        if idea:
            st.markdown(f"<div class='idea-card' style='font-size:0.85rem; line-height:1.7;'>{idea}</div>", unsafe_allow_html=True)
        else:
            st.caption("Sincroniza para generar ideas de IA.")

    with col_caption:
        st.markdown("#### ✍️ Caption listo")
        caption = _obtener_caption_hoy(captions_ia, plataforma)
        if caption:
            # Limpiar tag de plataforma del caption para mostrarlo limpio
            caption_limpio = re.sub(r'\[.*?\]\s*', '', caption, count=1).strip()
            # Renderizar como tarjeta editorial copiable
            caption_html = caption_limpio.replace('\n', '<br>')
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E8E3DA; border-radius:8px; padding:1.2rem; position:relative;">
                <p style="font-size:0.82rem; line-height:1.7; color:#4A453F; margin:0; white-space:pre-wrap;">{caption_html}</p>
                <div style="margin-top:0.8rem; padding-top:0.6rem; border-top:1px solid #F4F1EA; display:flex; align-items:center; gap:6px;">
                    <span style="font-size:0.65rem; color:#A39B8F; text-transform:uppercase; letter-spacing:1px;">📋 Selecciona y copia</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption("Los captions se generan con el motor de IA (lunes y jueves).")

    with col_estado:
        st.markdown("#### 📊 Tu estado")
        dias_ig = _dias_sin_publicar(df_metricas, 'instagram')
        dias_tt = _dias_sin_publicar(df_metricas, 'tiktok')
        dias_yt = _dias_sin_publicar(df_metricas, 'youtube')

        color_ig = "🟢" if dias_ig <= 1 else ("🟡" if dias_ig <= 3 else "🔴")
        color_tt = "🟢" if dias_tt <= 1 else ("🟡" if dias_tt <= 3 else "🔴")
        color_yt = "🟢" if dias_yt <= 7 else ("🟡" if dias_yt <= 14 else "🔴")

        st.markdown(f"{color_ig} IG: hace {dias_ig}d")
        st.markdown(f"{color_tt} TT: hace {dias_tt}d")
        st.markdown(f"{color_yt} YT: hace {dias_yt}d")

    st.markdown("<br>", unsafe_allow_html=True)

    # Razón del formato
    st.caption(f"💡 *¿Por qué {formato} hoy?* — {razon}")

    st.markdown("---")

    # Vista rápida de la semana (mini planificador visual)
    st.markdown("#### 📅 Tu semana de un vistazo")

    cols = st.columns(7)
    for i, col in enumerate(cols):
        with col:
            d = FORMATOS_DIA[i]
            dia_label = ['L', 'M', 'X', 'J', 'V', 'S', 'D'][i]
            es_hoy = (i == dia_semana)
            emoji_p = {'instagram': '📸', 'tiktok': '🎵', 'youtube': '📺'}[d['plataforma']]

            if es_hoy:
                st.markdown(f"<div style='text-align:center; background:#5C554B; color:white; border-radius:8px; padding:8px 4px;'><strong>{dia_label}</strong><br>{emoji_p}<br><span style='font-size:0.65rem;'>{d['formato'][:5]}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center; background:#F4F1EA; border-radius:8px; padding:8px 4px;'><strong>{dia_label}</strong><br>{emoji_p}<br><span style='font-size:0.65rem; color:#A39B8F;'>{d['formato'][:5]}</span></div>", unsafe_allow_html=True)

    # Distribución de esfuerzo
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("📐 **Distribución semanal:** Instagram 60% (4 días) · TikTok 30% (2 días) · YouTube 10% (1 día)")
