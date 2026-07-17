"""
Tracking de links en bio — correlación publicaciones → visitas a itsbgart.es

Sin Google Analytics integrado, usa una heurística:
- Los días que publicas contenido con CTA ("link en bio", "web", "tienda", etc.)
  se correlacionan con picos de tráfico potencial.
- Detecta qué publicaciones probablemente generaron visitas a la web.
"""

import re
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


# Palabras que indican que el post dirige tráfico a la web
KEYWORDS_CTA_BIO = [
    'link', 'bio', 'web', 'tienda', 'shop', 'etsy', 'itsbgart.es',
    'enlace', 'perfil', 'encargo', 'encargos', 'comisión', 'comisiones',
    'disponible', 'pedidos', 'compra', 'comprar'
]

WEB_URL = "www.itsbgart.es"


def _detectar_cta_bio(titulo):
    """Detecta si un post tiene CTA hacia la bio/web."""
    texto = str(titulo).lower()
    return any(kw in texto for kw in KEYWORDS_CTA_BIO)


def _calcular_score_trafico(row):
    """Score estimado de generación de tráfico basado en engagement + CTA."""
    tiene_cta = _detectar_cta_bio(row['titulo'])
    if not tiene_cta:
        return 0
    # Score: compartidos pesan mucho (gente enviando el link), guardados medio, likes poco
    return (row.get('compartidos', 0) * 3 + row.get('guardados', 0) * 2 + row.get('likes', 0) * 0.5)


def renderizar_bio_tracking(df):
    """Renderiza la sección de tracking de links en bio."""
    
    st.markdown("#### 🔗 Tracking de Tráfico a Web")
    st.markdown(f"<p style='font-size:0.8rem; color:#A39B8F;'>Posts que probablemente dirigen visitas a <strong>{WEB_URL}</strong></p>", unsafe_allow_html=True)

    if df.empty:
        st.caption("Sin datos suficientes.")
        return

    # Trabajar con los datos recibidos directamente (ya filtrados por plataforma)
    df_social = df.copy()
    
    if df_social.empty:
        st.caption("Sin datos de Instagram o TikTok.")
        return

    # Detectar posts con CTA
    df_social['tiene_cta'] = df_social['titulo'].apply(_detectar_cta_bio)
    df_social['score_trafico'] = df_social.apply(_calcular_score_trafico, axis=1)

    df_con_cta = df_social[df_social['tiene_cta']].copy()
    total_posts = len(df_social)
    posts_con_cta = len(df_con_cta)

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Posts con CTA a web", f"{posts_con_cta}/{total_posts}", delta=f"{posts_con_cta/max(total_posts,1)*100:.0f}% del total")
    with col_m2:
        if not df_con_cta.empty:
            media_vistas_cta = int(df_con_cta['visualizaciones'].mean())
            media_vistas_sin = int(df_social[~df_social['tiene_cta']]['visualizaciones'].mean()) if len(df_social[~df_social['tiene_cta']]) > 0 else 0
            diff = media_vistas_cta - media_vistas_sin
            st.metric("Media vistas (con CTA)", f"{media_vistas_cta:,}".replace(',', '.'), delta=f"{diff:+,} vs sin CTA".replace(',', '.'))
        else:
            st.metric("Media vistas (con CTA)", "—")
    with col_m3:
        if not df_con_cta.empty:
            eng_con = (df_con_cta['likes'] / df_con_cta['visualizaciones'].replace(0, 1) * 100).mean()
            eng_sin = (df_social[~df_social['tiene_cta']]['likes'] / df_social[~df_social['tiene_cta']]['visualizaciones'].replace(0, 1) * 100).mean() if len(df_social[~df_social['tiene_cta']]) > 0 else 0
            st.metric("Engagement (con CTA)", f"{eng_con:.1f}%", delta=f"{eng_con-eng_sin:+.1f}% vs sin CTA")
        else:
            st.metric("Engagement (con CTA)", "—")

    # Top posts que generan tráfico
    if not df_con_cta.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**🏆 Posts con mayor potencial de tráfico a la web:**")
        top_trafico = df_con_cta.sort_values('score_trafico', ascending=False).head(5)
        st.dataframe(
            top_trafico[['titulo', 'visualizaciones', 'compartidos', 'url']].rename(
                columns={'titulo': 'Obra', 'visualizaciones': '👁️', 'compartidos': '✈️'}
            ),
            column_config={"url": st.column_config.LinkColumn("🔗", display_text="Ver")},
            use_container_width=True, hide_index=True
        )

        # Recomendación
        st.markdown("<br>", unsafe_allow_html=True)
        if posts_con_cta / max(total_posts, 1) < 0.2:
            st.warning(f"💡 Solo el {posts_con_cta/max(total_posts,1)*100:.0f}% de tus posts dirigen a la web. Intenta incluir CTA en al menos 1 de cada 3 publicaciones para maximizar visitas a {WEB_URL}. La clave es que el sistema detecta estas palabras en el caption: link, bio, web, tienda, encargo, encargos, disponible, itsbgart.es, perfil, compra. Si alguna de ellas aparece en el texto, el post se cuenta como 'con CTA'. Así que la acción concreta es: en 1 de cada 3 publicaciones, añade una frase natural al final del caption que mencione su web o 'link en bio'. No hace falta en todas — con pasar del {posts_con_cta/max(total_posts,1)*100:.0f}% actual al ~30% ya es suficiente para generar tráfico consistente.")
        else:
            st.success(f"✅ Buen ratio de CTAs ({posts_con_cta/max(total_posts,1)*100:.0f}%). Sigue incluyendo referencias a {WEB_URL} en tu contenido.")
    else:
        st.info(f"💡 No se detectaron posts con CTA hacia la web. Incluye palabras como 'link en bio', 'tienda', '{WEB_URL}' en tus captions para dirigir tráfico.")
