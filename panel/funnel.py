"""
Funnel de conversión por post (Instagram y TikTok).

Muestra el embudo: Vistas → Likes → Comentarios → Guardados/Compartidos
para identificar qué posts "convierten" vs los que solo generan vistas vacías.
"""

import streamlit as st
import pandas as pd
import altair as alt


def _calcular_tasas_conversion(df):
    """Calcula tasas de conversión para cada post."""
    df_f = df.copy()
    df_f['tasa_like'] = (df_f['likes'] / df_f['visualizaciones'].replace(0, 1) * 100).round(2)
    df_f['tasa_comentario'] = (df_f['compartidos'] / df_f['visualizaciones'].replace(0, 1) * 100).round(2)
    df_f['tasa_guardado'] = (df_f['guardados'] / df_f['visualizaciones'].replace(0, 1) * 100).round(2)
    # Score de conversión: pondera guardados (5x) + compartidos (3x) + likes (1x)
    df_f['score_conversion'] = (
        df_f['guardados'] * 5 + df_f['compartidos'] * 3 + df_f['likes']
    ) / df_f['visualizaciones'].replace(0, 1) * 100
    df_f['score_conversion'] = df_f['score_conversion'].round(2)
    return df_f


def renderizar_funnel(df, plataforma):
    """Renderiza el funnel de conversión para una plataforma."""
    
    if df.empty or len(df) < 3:
        st.caption("Se necesitan al menos 3 publicaciones para analizar el funnel.")
        return

    df_f = _calcular_tasas_conversion(df)

    # Funnel global (medias)
    total_vistas = int(df_f['visualizaciones'].sum())
    total_likes = int(df_f['likes'].sum())
    total_compartidos = int(df_f['compartidos'].sum())
    total_guardados = int(df_f['guardados'].sum())

    st.markdown("#### 🔽 Funnel de Conversión")

    # Barras del funnel
    etapas = ['Vistas', 'Likes', 'Compartidos', 'Guardados'] if plataforma == 'instagram' else ['Vistas', 'Likes', 'Compartidos']
    valores = [total_vistas, total_likes, total_compartidos, total_guardados] if plataforma == 'instagram' else [total_vistas, total_likes, total_compartidos]
    
    max_val = max(valores) if valores else 1
    colores = ['#5C554B', '#7B7163', '#A39B8F', '#D1C8BA']

    for i, (etapa, valor) in enumerate(zip(etapas, valores)):
        pct = valor / max_val * 100
        tasa = valor / total_vistas * 100 if total_vistas > 0 else 0
        st.markdown(f"""
        <div style="margin-bottom:4px;">
            <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#7B7163;">
                <span>{etapa}</span>
                <span>{valor:,} ({tasa:.1f}%)</span>
            </div>
            <div style="background:#F4F1EA; border-radius:4px; height:24px; overflow:hidden;">
                <div style="background:{colores[i]}; width:{pct}%; height:100%; border-radius:4px; transition:width 0.3s;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Top posts por conversión vs Top posts por vistas vacías
    col_conv, col_vacias = st.columns(2)

    # Excluir Stories en Instagram (métricas no comparables)
    df_ranking = df_f[df_f['estilo_visual'] != 'Story'] if plataforma == 'instagram' else df_f

    with col_conv:
        st.markdown("**🏆 Mejor conversión** (alto engagement relativo)")
        top_conv = df_ranking.sort_values('score_conversion', ascending=False).head(5)
        st.dataframe(
            top_conv[['titulo', 'visualizaciones', 'score_conversion']].rename(
                columns={'titulo': 'Obra', 'visualizaciones': '👁️', 'score_conversion': '📈 Score'}
            ),
            use_container_width=True, hide_index=True
        )

    with col_vacias:
        st.markdown("**⚠️ Vistas vacías** (muchas vistas, poco engagement)")
        # Posts con muchas vistas pero score de conversión bajo
        df_alto_vistas = df_ranking[df_ranking['visualizaciones'] >= df_ranking['visualizaciones'].median()]
        if not df_alto_vistas.empty:
            peor_conv = df_alto_vistas.sort_values('score_conversion').head(5)
            st.dataframe(
                peor_conv[['titulo', 'visualizaciones', 'score_conversion']].rename(
                    columns={'titulo': 'Obra', 'visualizaciones': '👁️', 'score_conversion': '📈 Score'}
                ),
                use_container_width=True, hide_index=True
            )
        else:
            st.caption("No hay suficientes datos.")

    # Insight
    media_score = df_f['score_conversion'].mean()
    st.caption(f"💡 Score medio de conversión: **{media_score:.1f}%** — Cuanto mayor, más \"valioso\" es tu alcance (tu audiencia actúa, no solo mira).")
