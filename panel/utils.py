"""Funciones auxiliares reutilizables del panel."""

import re
import streamlit as st
import pandas as pd
import altair as alt
from collections import Counter
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ_MADRID = ZoneInfo("Europe/Madrid")
DIAS_ES = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
}


def renderizar_etiquetas_visuales(texto):
    """Convierte etiquetas [VIDEO LARGO] etc en badges HTML."""
    texto = texto.replace("**[VIDEO LARGO]**", "[VIDEO LARGO]").replace("**[SHORT]**", "[SHORT]")
    texto = texto.replace("**[TIKTOK VERTICAL]**", "[TIKTOK VERTICAL]").replace("**[CARRUSEL]**", "[CARRUSEL]")
    texto = texto.replace("**[REEL]**", "[REEL]").replace("**[STORY]**", "[STORY]")
    texto = texto.replace("[VIDEO LARGO]", "\n\n<span class='badge-largo'>▶ VÍDEO LARGO</span>")
    texto = texto.replace("[SHORT]", "\n\n<span class='badge-corto'>📱 SHORT</span>")
    texto = texto.replace("[TIKTOK VERTICAL]", "\n\n<span class='badge-corto'>📱 VERTICAL</span>")
    texto = texto.replace("[REEL]", "\n\n<span class='badge-corto'>🎬 REEL</span>")
    texto = texto.replace("[STORY]", "\n\n<span class='badge-foto'>🤳 STORY</span>")
    texto = texto.replace("[CARRUSEL]", "\n\n<span class='badge-foto'>🖼️ CARRUSEL</span>")
    texto = texto.replace("\n- ", "\n\n- ").replace("\n* ", "\n\n- ")
    return texto


def extraer_palabras_exito(df, top_n=5, modo='texto'):
    """Extrae palabras clave de publicaciones exitosas con filtrado agresivo."""
    if df.empty:
        return []
    media_vistas = df['visualizaciones'].mean()
    df_exito = df[df['visualizaciones'] >= media_vistas]
    if len(df_exito) < 3:
        df_exito = df
    texto_completo = " ".join(df_exito['titulo'].dropna().tolist()).lower()

    if modo == 'hashtags':
        palabras = re.findall(r'#\w+', texto_completo)
        palabras = [p.replace('#', '') for p in palabras]
        basura = {"art", "arte", "artist", "artista", "illustration", "ilustracion", "drawing", "dibujo",
                  "painting", "pintura", "creative", "creativo", "love", "instagood", "photooftheday",
                  "follow", "like", "reels", "tiktok", "viral", "fyp", "parati", "foryou", "explore"}
        palabras = [p for p in palabras if p not in basura and len(p) > 3]
    else:
        stop_words = {"para", "como", "cómo", "este", "esta", "estos", "estas", "esos", "esas", "pero", "porque",
                      "cuando", "desde", "hasta", "sobre", "también", "solo", "todo", "nada", "mucho", "poco",
                      "algo", "otro", "otra", "otros", "aquí", "ahí", "donde", "quien", "cada", "hacer", "haciendo",
                      "hecho", "siendo", "tener", "tiene", "vamos", "saber", "poder", "querer", "decir",
                      "subiendo", "subido", "publicando", "compartiendo", "hoy", "día", "días", "vez", "veces",
                      "semana", "hora", "rato", "mañana", "tarde", "noche", "ahora", "siempre", "nunca",
                      "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                      "octubre", "noviembre", "diciembre", "vlog", "video", "vídeo", "post", "story", "reel",
                      "foto", "clip", "parte", "nuevo", "nueva", "bueno", "buena", "mejor", "peor", "gran",
                      "grande", "pequeño", "primer", "primera", "instagram", "tiktok", "youtube", "shorts",
                      "coche", "camino", "casa", "cosa", "gente", "mundo", "vida", "aunque", "mientras",
                      "entonces", "después", "antes"}
        palabras_raw = re.findall(r'\b[a-záéíóúñü]{4,}\b', texto_completo)
        palabras = [p for p in palabras_raw if p not in stop_words]

    contador = Counter(palabras)
    return [palabra for palabra, frec in contador.most_common(top_n) if frec >= 2]


def calcular_delta(df_all, metrica, dias_actual=7):
    """Calcula delta porcentual entre periodo actual y anterior."""
    hoy = datetime.now()
    actual = df_all[df_all['fecha_publicacion'] >= hoy - timedelta(days=dias_actual)]
    anterior = df_all[(df_all['fecha_publicacion'] >= hoy - timedelta(days=dias_actual * 2)) & (df_all['fecha_publicacion'] < hoy - timedelta(days=dias_actual))]
    if actual.empty or anterior.empty:
        return None
    val_actual = actual[metrica].sum()
    val_anterior = anterior[metrica].sum()
    if val_anterior == 0:
        return None
    return f"{((val_actual - val_anterior) / val_anterior * 100):+.0f}%"


def renderizar_kpis(df, df_all):
    """Renderiza los 4 KPIs principales con deltas."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Exposición (Vistas)", f"{df['visualizaciones'].sum():,}".replace(',', '.'), delta=calcular_delta(df_all, 'visualizaciones'))
    col2.metric("Interacciones (Likes)", f"{df['likes'].sum():,}".replace(',', '.'), delta=calcular_delta(df_all, 'likes'))
    col3.metric("Obras en Periodo", len(df['titulo'].unique()))
    eng = (df['likes'] / df['visualizaciones'].replace(0, 1) * 100).mean()
    col4.metric("Engagement Promedio", f"{eng:.2f}%")


def renderizar_mejor_hora(df, plataforma_nombre):
    """Muestra la mejor hora de publicación para una plataforma."""
    if len(df) < 3:
        st.caption("Pocos datos para analizar la mejor hora.")
        return
    df_h = df.copy()
    df_h['hora'] = df_h['fecha_publicacion'].dt.tz_localize('UTC').dt.tz_convert(TZ_MADRID).dt.hour
    df_h['dia'] = df_h['fecha_publicacion'].dt.day_name()
    eng_hora = df_h.groupby('hora')[['engagement_pct']].mean().reset_index()

    if eng_hora.empty:
        return

    mejor_h = int(eng_hora.loc[eng_hora['engagement_pct'].idxmax(), 'hora'])
    eng_dia = df_h.groupby('dia')['engagement_pct'].mean()
    mejor_dia = DIAS_ES.get(eng_dia.idxmax(), eng_dia.idxmax()) if not eng_dia.empty else "—"

    col_g, col_r = st.columns([3, 1])
    with col_g:
        grafico = alt.Chart(eng_hora).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X('hora:O', title='Hora (Madrid)'),
            y=alt.Y('engagement_pct:Q', title='Engagement %'),
            color=alt.condition(alt.datum.hora == mejor_h, alt.value('#5C554B'), alt.value('#D1C8BA')),
            tooltip=['hora', alt.Tooltip('engagement_pct:Q', format='.2f')]
        ).properties(height=200)
        st.altair_chart(grafico, use_container_width=True)
    with col_r:
        st.markdown(f"⭐ **Mejor hora:** {mejor_h:02d}:00")
        st.markdown(f"📅 **Mejor día:** {mejor_dia}")


def renderizar_tabla_contenidos(df):
    """Muestra la tabla de contenidos con enlaces."""
    df_tabla = df[['titulo', 'estilo_visual', 'fecha_publicacion', 'visualizaciones', 'likes', 'url']].copy()
    df_tabla['fecha_publicacion'] = df_tabla['fecha_publicacion'].dt.strftime('%Y-%m-%d')
    st.dataframe(
        df_tabla.rename(columns={'titulo': 'Obra', 'estilo_visual': 'Formato', 'fecha_publicacion': 'Fecha', 'visualizaciones': '👁️', 'likes': '❤️'}),
        column_config={"url": st.column_config.LinkColumn("🔗", display_text="Ver")},
        use_container_width=True, hide_index=True
    )
