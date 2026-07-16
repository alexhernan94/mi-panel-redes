import streamlit as st
import pandas as pd
import altair as alt
import warnings
import re
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from conexion import obtener_conexion
from procesamiento.motor_ia import analizar_y_generar_ideas
from extraccion.instagram import extraer_instagram
from extraccion.tiktok import extraer_y_guardar_tiktok
from extraccion.youtube import extraer_youtube
from panel import (
    verificar_contrasena,
    cargar_datos_panel,
    renderizar_etiquetas_visuales,
    extraer_palabras_exito,
    calcular_delta,
    renderizar_kpis,
    renderizar_mejor_hora,
    renderizar_tabla_contenidos,
    TZ_MADRID,
    DIAS_ES,
    ESTILO_EDITORIAL,
)
from panel.objetivos import renderizar_objetivos

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Analítica | itsbgart", page_icon="✨", layout="wide")

# --- AUTENTICACIÓN ---
if not verificar_contrasena():
    st.stop()

# --- ESTILOS ---
st.markdown(ESTILO_EDITORIAL, unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 style='text-align: left;'>itsbgart <span style='font-family: Montserrat; font-size: 1.3rem; color: #A39B8F; font-weight:300; letter-spacing:1px;'> | CUADRO DE MANDOS</span></h1>", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
df_metricas, df_ia = cargar_datos_panel()

if df_metricas.empty:
    st.error("Error al conectar con la base de datos o sin datos disponibles.")
    st.stop()

# --- PREPARACIÓN DE DATOS ---
df_metricas['visualizaciones'] = df_metricas['visualizaciones'].fillna(0).astype(int)
df_metricas['likes'] = df_metricas['likes'].fillna(0).astype(int)
df_metricas['compartidos'] = df_metricas['compartidos'].fillna(0).astype(int)
df_metricas['guardados'] = df_metricas['guardados'].fillna(0).astype(int)
df_metricas['estilo_visual'] = df_metricas['estilo_visual'].fillna('Vídeo')
df_metricas['fecha_publicacion'] = pd.to_datetime(df_metricas['fecha_publicacion'])
df_metricas['engagement_pct'] = (df_metricas['likes'] / df_metricas['visualizaciones'].replace(0, 1) * 100).fillna(0)

# --- FILTROS GLOBALES ---
st.markdown("<hr style='border: 0; height: 1px; background: #E8E3DA; margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
col_ft, col_fb = st.columns([2, 1])
with col_ft:
    opcion_tiempo = st.radio("📅 Filtrar", ("Todo el histórico", "Últimos 30 días", "Últimos 7 días"), horizontal=True, label_visibility="collapsed")
with col_fb:
    busqueda = st.text_input("🔍 Buscar", placeholder="Ej. vlog, pintura, marruecos...", label_visibility="collapsed")

if opcion_tiempo == "Últimos 30 días":
    fecha_limite = datetime.now() - timedelta(days=30)
    df_filtrado = df_metricas[df_metricas['fecha_publicacion'] >= fecha_limite]
elif opcion_tiempo == "Últimos 7 días":
    fecha_limite = datetime.now() - timedelta(days=7)
    df_filtrado = df_metricas[df_metricas['fecha_publicacion'] >= fecha_limite]
else:
    df_filtrado = df_metricas.copy()

if busqueda:
    df_filtrado = df_filtrado[df_filtrado['titulo'].str.contains(busqueda, case=False, na=False)]

if df_filtrado.empty:
    st.warning("No hay resultados para los filtros seleccionados.")
    st.stop()

# --- PARSEO IA ---
ideas_yt, ideas_tt, ideas_ig = "Generando ideas...", "Generando ideas...", "Generando ideas..."
planificador_semanal = ""
captions_ia = ""
if not df_ia.empty:
    ideas_raw = df_ia.iloc[0].get('ideas_contenido', '')
    match_yt = re.search(r'\[YOUTUBE\](.*?)\[TIKTOK\]', str(ideas_raw), re.DOTALL)
    match_tt = re.search(r'\[TIKTOK\](.*?)\[INSTAGRAM\]', str(ideas_raw), re.DOTALL)
    match_ig = re.search(r'\[INSTAGRAM\](.*?)(\[PLANIFICADOR|$)', str(ideas_raw), re.DOTALL)
    if match_yt: ideas_yt = match_yt.group(1).strip()
    if match_tt: ideas_tt = match_tt.group(1).strip()
    if match_ig: ideas_ig = match_ig.group(1).strip()
    if '[PLANIFICADOR SEMANAL]' in str(ideas_raw):
        parte_plan = str(ideas_raw).split('[PLANIFICADOR SEMANAL]')[1]
        if '[CAPTIONS]' in parte_plan:
            planificador_semanal = parte_plan.split('[CAPTIONS]')[0].strip()
            captions_ia = parte_plan.split('[CAPTIONS]')[1].strip()
        else:
            planificador_semanal = parte_plan.strip()

# --- PESTAÑAS PRINCIPALES ---
tab_general, tab_ig, tab_tt, tab_yt = st.tabs(["📊 General", "📸 Instagram", "🎵 TikTok", "📺 YouTube"])


# ============================================================
# PESTAÑA GENERAL
# ============================================================
with tab_general:
    # Botón sincronizar
    col_vacia, col_boton = st.columns([4, 1])
    with col_boton:
        if st.button("🔄 Sincronizar Ahora", use_container_width=True):
            with st.spinner("📡 Extrayendo datos frescos..."):
                errores = []
                try: extraer_instagram(); st.toast("✅ Instagram")
                except Exception as e: errores.append(f"Instagram: {e}")
                try: extraer_y_guardar_tiktok(); st.toast("✅ TikTok")
                except Exception as e: errores.append(f"TikTok: {e}")
                try: extraer_youtube(); st.toast("✅ YouTube")
                except Exception as e: errores.append(f"YouTube: {e}")
            with st.spinner("🧠 Generando estrategia IA..."):
                try: analizar_y_generar_ideas(); st.toast("✅ IA")
                except Exception as e: errores.append(f"Motor IA: {e}")
            if errores:
                st.warning("Errores:\n" + "\n".join(f"- {e}" for e in errores))
            st.cache_data.clear()
            st.rerun()

    # KPIs globales
    renderizar_kpis(df_filtrado, df_metricas)
    st.markdown("<br>", unsafe_allow_html=True)

    # IA Insights
    st.markdown("### 🧠 Insights de IA")
    if not df_ia.empty:
        tendencias = df_ia.iloc[0].get('tendencias_actuales', '')
        analisis = df_ia.iloc[0].get('analisis_rendimiento', '')
        if tendencias:
            st.success("**🌊 Tendencias de la semana:**\n\n" + tendencias)
        if analisis:
            st.info("**📈 Lectura de rendimiento:**\n\n" + analisis)
        if len(df_ia) > 1:
            with st.expander(f"📜 Análisis anteriores ({len(df_ia)-1})"):
                for _, row in df_ia.iloc[1:].iterrows():
                    fecha_g = pd.to_datetime(row.get('fecha_generacion')).strftime('%d/%m/%Y') if pd.notna(row.get('fecha_generacion')) else '—'
                    st.caption(f"**{fecha_g}:** {str(row['analisis_rendimiento'])[:150]}...")
    else:
        st.info("Pulsa 'Sincronizar Ahora' para generar el primer análisis.")

    st.markdown("---")

    # Planificador semanal
    if planificador_semanal:
        st.markdown("### 📋 Planificador Semanal")
        lineas = [l.strip() for l in planificador_semanal.split('\n') if l.strip()]
        dias_plan = []
        justificacion = ""
        for linea in lineas:
            if linea.startswith('- ') or linea.startswith('• '):
                dias_plan.append(linea.lstrip('- •').strip())
            elif linea.lower().startswith('justific'):
                justificacion = linea.split(':', 1)[1].strip() if ':' in linea else linea
            elif not dias_plan:
                continue
            else:
                justificacion += " " + linea
        if dias_plan:
            emojis_dias = {'lunes':'🟡','martes':'🔵','miércoles':'🟢','jueves':'🟣','viernes':'🔴','sábado':'🟠','domingo':'⚪'}
            for dia_linea in dias_plan:
                dia_nombre = dia_linea.split(':')[0].strip().lower() if ':' in dia_linea else ''
                emoji = emojis_dias.get(dia_nombre, '📌')
                st.markdown(f"{emoji} **{dia_linea}**")
            if justificacion.strip():
                st.caption(f"💡 {justificacion.strip()}")
        else:
            st.markdown(planificador_semanal)
        st.markdown("---")

    # Captions generados por IA
    if captions_ia:
        st.markdown("### ✍️ Captions Listos para Usar")
        st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>Generados por IA, optimizados para engagement. Copia y pega.</p>", unsafe_allow_html=True)
        captions_lineas = captions_ia.split('\n')
        caption_actual = ""
        for linea in captions_lineas:
            linea = linea.strip()
            if not linea:
                continue
            if linea[0].isdigit() and '.' in linea[:3]:
                if caption_actual:
                    st.code(caption_actual.strip(), language=None)
                caption_actual = linea.split('.', 1)[1].strip() + "\n"
            else:
                caption_actual += linea + "\n"
        if caption_actual:
            st.code(caption_actual.strip(), language=None)
        st.markdown("---")

    # Objetivos de crecimiento
    try:
        con_obj = obtener_conexion()
        if con_obj:
            df_seg_obj = pd.read_sql("SELECT plataforma, seguidores, fecha_registro FROM seguidores_historico ORDER BY fecha_registro", con_obj)
            con_obj.close()
            df_seg_obj['fecha_registro'] = pd.to_datetime(df_seg_obj['fecha_registro'])
            renderizar_objetivos(df_seg_obj)
        else:
            renderizar_objetivos(pd.DataFrame())
    except Exception:
        st.caption("Tabla de objetivos no disponible. Ejecuta `migracion_objetivos.sql` en phpMyAdmin.")
    st.markdown("---")

    # Mejor hora por plataforma
    st.markdown("### 🕐 Mejor Hora para Publicar")
    cols_hora = st.columns(3)
    for i, (plat, emoji) in enumerate([('instagram','📸'), ('tiktok','🎵'), ('youtube','📺')]):
        with cols_hora[i]:
            st.markdown(f"**{emoji} {plat.capitalize()}**")
            df_plat_h = df_filtrado[df_filtrado['plataforma'] == plat]
            renderizar_mejor_hora(df_plat_h, plat)

    st.markdown("---")

    # Anomalías por plataforma
    st.markdown("### 🚨 Anomalías Detectadas")
    for plat in df_filtrado['plataforma'].unique():
        df_a = df_filtrado[df_filtrado['plataforma'] == plat]
        if len(df_a) < 5:
            continue
        media_v = df_a['visualizaciones'].mean()
        std_v = df_a['visualizaciones'].std()
        virales = df_a[df_a['visualizaciones'] > media_v + 2 * std_v]
        emoji = "📸" if plat == "instagram" else ("🎵" if plat == "tiktok" else "📺")
        if not virales.empty:
            st.success(f"🔥 **{emoji} {plat.capitalize()}:** {len(virales)} post(s) viral(es)")
            for _, r in virales.head(2).iterrows():
                st.caption(f"• {r['titulo'][:50]} → {r['visualizaciones']:,} vistas")

    st.markdown("---")

    # Calendario editorial
    st.markdown("### 📆 Calendario Editorial (últimos 30 días)")
    fecha_cal = datetime.now() - timedelta(days=30)
    df_cal = df_metricas[df_metricas['fecha_publicacion'] >= fecha_cal].copy()
    df_cal['fecha'] = df_cal['fecha_publicacion'].dt.date
    posts_dia = df_cal.groupby('fecha').size().reset_index(name='posts')
    todos_dias = pd.DataFrame({'fecha': pd.date_range(start=fecha_cal, end=datetime.now(), freq='D').date})
    df_calendario = todos_dias.merge(posts_dia, on='fecha', how='left')
    df_calendario['posts'] = df_calendario['posts'].fillna(0).astype(int)
    df_calendario['fecha_dt'] = pd.to_datetime(df_calendario['fecha'])

    cal_chart = alt.Chart(df_calendario).mark_rect(cornerRadius=3).encode(
        x=alt.X('date(fecha_dt):O', title='Día'),
        y=alt.Y('month(fecha_dt):O', title=''),
        color=alt.Color('posts:Q', scale=alt.Scale(scheme='greens'), title='Posts'),
        tooltip=['fecha', 'posts']
    ).properties(height=100)
    st.altair_chart(cal_chart, use_container_width=True)
    dias_sin = df_calendario[df_calendario['posts'] == 0]
    st.caption(f"📌 {len(dias_sin)} días sin publicar. Cadencia: ~1 post cada {30/max(len(posts_dia),1):.1f} días")

    st.markdown("---")

    # Evergreen
    st.markdown("### 🌿 Contenido Evergreen")
    fecha_ev = datetime.now() - timedelta(days=14)
    df_ev = df_metricas[df_metricas['fecha_publicacion'] <= fecha_ev].copy()
    if len(df_ev) >= 3:
        df_ev['dias_vida'] = (datetime.now() - df_ev['fecha_publicacion']).dt.days
        df_ev['vistas_dia'] = (df_ev['visualizaciones'] / df_ev['dias_vida']).round(1)
        top_ev = df_ev.sort_values('vistas_dia', ascending=False).head(5)
        st.dataframe(
            top_ev[['plataforma','titulo','estilo_visual','dias_vida','visualizaciones','vistas_dia','url']].rename(columns={'plataforma':'Red','titulo':'Obra','estilo_visual':'Formato','dias_vida':'📅 Días','visualizaciones':'👁️ Vistas','vistas_dia':'📈/día'}),
            column_config={"url": st.column_config.LinkColumn("🔗", display_text="Ver")},
            use_container_width=True, hide_index=True
        )
    else:
        st.caption("Se necesitan posts con +14 días para detectar evergreen.")

    st.markdown("---")

    # Benchmark
    st.markdown("### 📏 Tu Engagement vs Sector")
    benchmarks = {'instagram': 1.5, 'tiktok': 3.0, 'youtube': 2.0}
    cols_b = st.columns(3)
    for i, (plat, ref) in enumerate(benchmarks.items()):
        with cols_b[i]:
            df_b = df_filtrado[df_filtrado['plataforma'] == plat]
            if not df_b.empty:
                tu_eng = df_b['engagement_pct'].mean()
                st.metric(f"{'📸' if plat=='instagram' else '🎵' if plat=='tiktok' else '📺'} {plat.capitalize()}", f"{tu_eng:.2f}%", delta=f"{tu_eng-ref:+.2f}% vs {ref}%")
            else:
                st.metric(plat.capitalize(), "—")

    st.markdown("---")

    # Crecimiento de seguidores
    st.markdown("### 👥 Crecimiento de Seguidores")
    try:
        con_seg = obtener_conexion()
        if con_seg:
            df_seguidores = pd.read_sql("SELECT plataforma, seguidores, fecha_registro FROM seguidores_historico ORDER BY fecha_registro", con_seg)
            con_seg.close()

            if not df_seguidores.empty:
                df_seguidores['fecha_registro'] = pd.to_datetime(df_seguidores['fecha_registro'])

                chart_seg = alt.Chart(df_seguidores).mark_line(point=True, strokeWidth=2).encode(
                    x=alt.X('fecha_registro:T', title='Fecha'),
                    y=alt.Y('seguidores:Q', title='Seguidores'),
                    color=alt.Color('plataforma:N', scale=alt.Scale(scheme='set2'), title='Plataforma'),
                    tooltip=['plataforma', 'fecha_registro', 'seguidores']
                ).properties(height=250)
                st.altair_chart(chart_seg, use_container_width=True)

                cols_seg = st.columns(3)
                for i, plat in enumerate(['instagram', 'tiktok', 'youtube']):
                    with cols_seg[i]:
                        df_plat_seg = df_seguidores[df_seguidores['plataforma'] == plat].sort_values('fecha_registro')
                        if len(df_plat_seg) >= 1:
                            ultimo = int(df_plat_seg.iloc[-1]['seguidores'])
                            emoji = "📸" if plat == "instagram" else ("🎵" if plat == "tiktok" else "📺")
                            delta_seg = None
                            if len(df_plat_seg) >= 2:
                                anterior = int(df_plat_seg.iloc[-2]['seguidores'])
                                if anterior > 0:
                                    delta_seg = f"{ultimo - anterior:+d} ({(ultimo-anterior)/anterior*100:+.1f}%)"
                            st.metric(f"{emoji} {plat.capitalize()}", f"{ultimo:,}".replace(',','.'), delta=delta_seg)
            else:
                st.caption("Los datos de seguidores se empezarán a acumular con cada sincronización. Vuelve mañana para ver la evolución.")
    except Exception:
        st.caption("Tabla de seguidores no disponible. Ejecuta `migracion_seguidores.sql` en phpMyAdmin.")

    st.markdown("---")

    # Correlación contenido-crecimiento
    st.markdown("### 📈 Correlación Contenido → Crecimiento")
    try:
        if 'df_seguidores' in dir() and not df_seguidores.empty:
            df_pub_dias = df_metricas.copy()
            df_pub_dias['fecha'] = df_pub_dias['fecha_publicacion'].dt.date
            pub_por_dia = df_pub_dias.groupby('fecha').agg(
                posts=('titulo', 'count'),
                vistas_totales=('visualizaciones', 'sum'),
                mejor_post=('titulo', 'first')
            ).reset_index()
            pub_por_dia['fecha'] = pd.to_datetime(pub_por_dia['fecha'])

            df_seg_total = df_seguidores.groupby('fecha_registro')['seguidores'].sum().reset_index()
            df_seg_total['crecimiento'] = df_seg_total['seguidores'].diff()
            df_seg_total = df_seg_total.rename(columns={'fecha_registro': 'fecha'})

            df_correlacion = pub_por_dia.merge(df_seg_total[['fecha', 'crecimiento']], on='fecha', how='inner')

            if not df_correlacion.empty and df_correlacion['crecimiento'].notna().any():
                top_crecimiento = df_correlacion[df_correlacion['crecimiento'] > 0].sort_values('crecimiento', ascending=False).head(5)
                if not top_crecimiento.empty:
                    st.markdown("**Días con mayor crecimiento de seguidores y qué publicaste:**")
                    for _, row in top_crecimiento.iterrows():
                        st.markdown(f"- **{row['fecha'].strftime('%d/%m')}**: +{int(row['crecimiento'])} seguidores — Publicaste {int(row['posts'])} post(s), top: *{row['mejor_post'][:40]}*")
                else:
                    st.caption("Aún no hay suficientes datos para correlacionar. Se necesitan varios días de sincronización.")
            else:
                st.caption("Se necesitan al menos 2 días de datos de seguidores para calcular correlaciones.")
        else:
            st.caption("Sincroniza durante varios días para ver la correlación contenido → crecimiento.")
    except Exception:
        st.caption("Los datos de crecimiento se irán acumulando con cada sincronización diaria.")

    st.markdown("---")

    # Análisis de hashtags por rendimiento
    st.markdown("### #️⃣ Hashtags por Rendimiento")
    st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>Hashtags que correlacionan con mayor alcance (no los más usados, sino los que mejor funcionan).</p>", unsafe_allow_html=True)

    df_hashtags = df_filtrado[df_filtrado['titulo'].str.contains('#', na=False)].copy()

    if not df_hashtags.empty:
        hashtag_rendimiento = {}
        for _, row in df_hashtags.iterrows():
            tags = re.findall(r'#(\w+)', str(row['titulo']).lower())
            for tag in tags:
                if len(tag) > 3:
                    if tag not in hashtag_rendimiento:
                        hashtag_rendimiento[tag] = {'vistas': [], 'likes': [], 'usos': 0}
                    hashtag_rendimiento[tag]['vistas'].append(row['visualizaciones'])
                    hashtag_rendimiento[tag]['likes'].append(row['likes'])
                    hashtag_rendimiento[tag]['usos'] += 1

        hashtag_stats = []
        for tag, data in hashtag_rendimiento.items():
            if data['usos'] >= 2:
                hashtag_stats.append({
                    'hashtag': f"#{tag}",
                    'usos': data['usos'],
                    'media_vistas': int(sum(data['vistas']) / len(data['vistas'])),
                    'media_likes': int(sum(data['likes']) / len(data['likes'])),
                    'engagement': round(sum(data['likes']) / max(sum(data['vistas']), 1) * 100, 2)
                })

        if hashtag_stats:
            df_hash_stats = pd.DataFrame(hashtag_stats)
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.markdown("**🔥 Top hashtags por alcance (vistas)**")
                top_vistas = df_hash_stats.sort_values('media_vistas', ascending=False).head(8)
                st.dataframe(
                    top_vistas[['hashtag', 'usos', 'media_vistas', 'engagement']].rename(columns={'hashtag':'#','usos':'Veces','media_vistas':'Media vistas','engagement':'Eng %'}),
                    use_container_width=True, hide_index=True
                )
            with col_h2:
                st.markdown("**💎 Top hashtags por engagement**")
                top_eng = df_hash_stats.sort_values('engagement', ascending=False).head(8)
                st.dataframe(
                    top_eng[['hashtag', 'usos', 'media_likes', 'engagement']].rename(columns={'hashtag':'#','usos':'Veces','media_likes':'Media likes','engagement':'Eng %'}),
                    use_container_width=True, hide_index=True
                )
        else:
            st.caption("No hay hashtags con 2+ usos para analizar su rendimiento.")
    else:
        st.caption("No se encontraron publicaciones con hashtags en este periodo.")



# ============================================================
# PESTAÑA INSTAGRAM
# ============================================================
with tab_ig:
    df_ig = df_filtrado[df_filtrado['plataforma'] == 'instagram']

    if df_ig.empty:
        st.info("Sin datos de Instagram para este periodo.")
    else:
        renderizar_kpis(df_ig, df_metricas[df_metricas['plataforma'] == 'instagram'])
        st.markdown("<br>", unsafe_allow_html=True)

        col_datos_ig, col_strat_ig = st.columns([3, 2], gap="large")

        with col_datos_ig:
            st.markdown("#### 📈 Evolución")
            df_ig_agr = df_ig.groupby('fecha_publicacion')['visualizaciones'].sum().reset_index()
            chart_ig = alt.Chart(df_ig_agr).mark_line(point=True, strokeWidth=2, color='#D1C8BA').encode(
                x=alt.X('fecha_publicacion:T', title=''),
                y=alt.Y('visualizaciones:Q', title='Vistas'),
                tooltip=['fecha_publicacion', 'visualizaciones']
            ).properties(height=250)
            st.altair_chart(chart_ig, use_container_width=True)

            st.markdown("#### 📋 Contenidos")
            renderizar_tabla_contenidos(df_ig)

        with col_strat_ig:
            st.markdown("#### 🕐 Mejor Hora")
            renderizar_mejor_hora(df_ig, 'instagram')

            claves = extraer_palabras_exito(df_ig, top_n=5, modo='texto')
            if claves:
                st.markdown("<p style='font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F; font-weight:600;'>✨ Conceptos Clave</p>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='badge-keyword'>#{p}</span>" for p in claves]), unsafe_allow_html=True)

            st.markdown("#### 💡 Dirección Creativa")
            st.markdown(f"<div class='idea-card' style='font-size:0.85rem; line-height:1.6;'>{renderizar_etiquetas_visuales(ideas_ig)}</div>", unsafe_allow_html=True)

        # Métricas avanzadas Instagram
        st.markdown("---")
        st.markdown("#### 💾 Métricas de Valor (Guardados y Compartidos)")
        col_guard, col_comp = st.columns(2)
        with col_guard:
            top_guardados = df_ig.sort_values('guardados', ascending=False).head(5)
            if top_guardados['guardados'].sum() > 0:
                st.dataframe(top_guardados[['titulo','guardados','likes']].rename(columns={'titulo':'Obra','guardados':'💾','likes':'❤️'}), use_container_width=True, hide_index=True)
            else:
                st.caption("Sin datos de guardados disponibles.")
        with col_comp:
            top_compartidos = df_ig.sort_values('compartidos', ascending=False).head(5)
            if top_compartidos['compartidos'].sum() > 0:
                st.dataframe(top_compartidos[['titulo','compartidos','likes']].rename(columns={'titulo':'Obra','compartidos':'✈️','likes':'❤️'}), use_container_width=True, hide_index=True)
            else:
                st.caption("Sin datos de compartidos disponibles.")


# ============================================================
# PESTAÑA TIKTOK
# ============================================================
with tab_tt:
    df_tt = df_filtrado[df_filtrado['plataforma'] == 'tiktok']

    if df_tt.empty:
        st.info("Sin datos de TikTok para este periodo.")
    else:
        renderizar_kpis(df_tt, df_metricas[df_metricas['plataforma'] == 'tiktok'])
        st.markdown("<br>", unsafe_allow_html=True)

        col_datos_tt, col_strat_tt = st.columns([3, 2], gap="large")

        with col_datos_tt:
            st.markdown("#### 📈 Evolución")
            df_tt_agr = df_tt.groupby('fecha_publicacion')['visualizaciones'].sum().reset_index()
            chart_tt = alt.Chart(df_tt_agr).mark_line(point=True, strokeWidth=2, color='#5C554B').encode(
                x=alt.X('fecha_publicacion:T', title=''),
                y=alt.Y('visualizaciones:Q', title='Vistas'),
                tooltip=['fecha_publicacion', 'visualizaciones']
            ).properties(height=250)
            st.altair_chart(chart_tt, use_container_width=True)

            st.markdown("#### 📋 Contenidos")
            renderizar_tabla_contenidos(df_tt)

        with col_strat_tt:
            st.markdown("#### 🕐 Mejor Hora")
            renderizar_mejor_hora(df_tt, 'tiktok')

            claves_tt = extraer_palabras_exito(df_tt, top_n=5, modo='hashtags')
            if claves_tt:
                st.markdown("<p style='font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F; font-weight:600;'>🎯 Hashtags de Éxito</p>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='badge-keyword'>#{p}</span>" for p in claves_tt]), unsafe_allow_html=True)

            st.markdown("#### 💡 Dirección Creativa")
            st.markdown(f"<div class='idea-card' style='font-size:0.85rem; line-height:1.6;'>{renderizar_etiquetas_visuales(ideas_tt)}</div>", unsafe_allow_html=True)

        # Rendimiento por formato TikTok
        st.markdown("---")
        st.markdown("#### 📊 Compartidos (señal de viralidad)")
        top_shares = df_tt.sort_values('compartidos', ascending=False).head(5)
        if top_shares['compartidos'].sum() > 0:
            st.dataframe(top_shares[['titulo','visualizaciones','likes','compartidos','url']].rename(
                columns={'titulo':'Obra','visualizaciones':'👁️','likes':'❤️','compartidos':'✈️'}),
                column_config={"url": st.column_config.LinkColumn("🔗", display_text="Ver")},
                use_container_width=True, hide_index=True)


# ============================================================
# PESTAÑA YOUTUBE
# ============================================================
with tab_yt:
    df_yt = df_filtrado[df_filtrado['plataforma'] == 'youtube']

    if df_yt.empty:
        st.info("Sin datos de YouTube para este periodo.")
    else:
        renderizar_kpis(df_yt, df_metricas[df_metricas['plataforma'] == 'youtube'])
        st.markdown("<br>", unsafe_allow_html=True)

        col_datos_yt, col_strat_yt = st.columns([3, 2], gap="large")

        with col_datos_yt:
            st.markdown("#### 📈 Evolución")
            df_yt_agr = df_yt.groupby('fecha_publicacion')['visualizaciones'].sum().reset_index()
            chart_yt = alt.Chart(df_yt_agr).mark_line(point=True, strokeWidth=2, color='#8C8273').encode(
                x=alt.X('fecha_publicacion:T', title=''),
                y=alt.Y('visualizaciones:Q', title='Vistas'),
                tooltip=['fecha_publicacion', 'visualizaciones']
            ).properties(height=250)
            st.altair_chart(chart_yt, use_container_width=True)

            st.markdown("#### 📋 Contenidos")
            df_yt_largos = df_yt[df_yt['estilo_visual'] == 'Vídeo largo']
            df_yt_shorts = df_yt[df_yt['estilo_visual'] == 'Short']

            if not df_yt_largos.empty:
                st.markdown("**▶ Vídeos Largos**")
                renderizar_tabla_contenidos(df_yt_largos)
            if not df_yt_shorts.empty:
                st.markdown("**📱 Shorts**")
                renderizar_tabla_contenidos(df_yt_shorts)

        with col_strat_yt:
            st.markdown("#### 🕐 Mejor Hora")
            renderizar_mejor_hora(df_yt, 'youtube')

            claves_yt = extraer_palabras_exito(df_yt, top_n=5, modo='texto')
            if claves_yt:
                st.markdown("<p style='font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F; font-weight:600;'>🔍 Palabras de Retención</p>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='badge-keyword'>#{p}</span>" for p in claves_yt]), unsafe_allow_html=True)

            st.markdown("#### 💡 Dirección Creativa")
            st.markdown(f"<div class='idea-card' style='font-size:0.85rem; line-height:1.6;'>{renderizar_etiquetas_visuales(ideas_yt)}</div>", unsafe_allow_html=True)

        # Comparativa Shorts vs Largos
        st.markdown("---")
        st.markdown("#### ⚖️ Shorts vs Vídeos Largos")
        col_sh, col_lg = st.columns(2)
        with col_sh:
            if not df_yt_shorts.empty:
                st.metric("📱 Shorts", f"{len(df_yt_shorts)} vídeos", delta=f"{df_yt_shorts['visualizaciones'].mean():,.0f} vistas/vídeo")
            else:
                st.metric("📱 Shorts", "0 vídeos")
        with col_lg:
            if not df_yt_largos.empty:
                st.metric("▶ Largos", f"{len(df_yt_largos)} vídeos", delta=f"{df_yt_largos['visualizaciones'].mean():,.0f} vistas/vídeo")
            else:
                st.metric("▶ Largos", "0 vídeos")
