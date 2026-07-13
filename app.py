import streamlit as st
import pandas as pd
import altair as alt
import warnings
import re
from collections import Counter
from datetime import datetime, timedelta
from conexion import obtener_conexion

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Analítica | itsbgart", page_icon="✨", layout="wide")

# --- SISTEMA DE AUTENTICACIÓN MAESTRO ---
def verificar_contrasena():
    """Devuelve True si el usuario ingresó la contraseña correcta."""
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if st.session_state["autenticado"]:
        return True

    # Pantalla de Login estética y minimalista
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_logo, col_login, col_espacio = st.columns([1, 2, 1])
    
    with col_login:
        st.markdown("<h2 style='text-align: center; font-family: Lora;'>itsbgart</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.8rem; color: #A39B8F; letter-spacing:1px;'>CUADRO DE MANDOS PRIVADO</p>", unsafe_allow_html=True)
        
        clave_introducida = st.text_input("Introduce la clave de acceso", type="password", placeholder="••••••••")
        
        # Leemos la contraseña secreta de las variables de entorno (.env en local o Secrets en la nube)
        clave_correcta = st.secrets.get("PANEL_PASSWORD") # Clave por defecto si no encuentra la variable
        

        if st.button("Entrar al Panel", use_container_width=True):
            if clave_introducida == clave_correcta:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta. Acceso denegado.")
                
    return False

# Si no pasa el control de seguridad, detenemos la ejecución de la app aquí
if not verificar_contrasena():
    st.stop()

# --- MAQUETACIÓN UX/UI ---
estilo_editorial = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;1,400&family=Montserrat:wght@300;400;500;600&display=swap');

    .stApp { background-color: #FDFBF7 !important; color: #4A453F !important; font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { font-family: 'Lora', serif !important; color: #5C554B !important; font-weight: 400 !important; }
    
    [data-testid="stMetric"] { background-color: #FFFFFF; border: 1px solid #E8E3DA; padding: 1.5rem; border-radius: 4px; box-shadow: 0 4px 12px rgba(92, 85, 75, 0.02); }
    [data-testid="stMetricValue"] { font-family: 'Lora', serif !important; color: #7B7163 !important; font-size: 2.3rem !important; }
    [data-testid="stMetricLabel"] { font-family: 'Montserrat', sans-serif !important; text-transform: uppercase; letter-spacing: 1.5px; font-size: 0.7rem !important; color: #A39B8F !important; }
    
    .bloque-ia { background-color: #FFFFFF; border-left: 3px solid #8C8273; border-top: 1px solid #E8E3DA; border-right: 1px solid #E8E3DA; border-bottom: 1px solid #E8E3DA; padding: 1.5rem; border-radius: 2px; margin-bottom: 1.5rem; }
    .idea-card { background-color: #F4F1EA; border: 1px solid #E8E3DA; padding: 1.2rem; border-radius: 4px; margin-top: 1rem; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 2.5rem; border-bottom: 1px solid #E8E3DA; }
    .stTabs [data-baseweb="tab"] { background-color: transparent !important; color: #A39B8F !important; font-family: 'Montserrat', sans-serif; text-transform: uppercase; font-size: 0.75rem; font-weight: 600; letter-spacing: 1px; padding-bottom: 0.8rem; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #7B7163 !important; color: #5C554B !important; }
    
    .badge-largo { background-color: #5C554B; color: #FFFFFF; padding: 3px 10px; border-radius: 12px; font-size: 0.65rem; font-weight: 600; letter-spacing: 0.5px; margin-right: 8px; }
    .badge-corto { background-color: #8C8273; color: #FFFFFF; padding: 3px 10px; border-radius: 12px; font-size: 0.65rem; font-weight: 600; letter-spacing: 0.5px; margin-right: 8px; }
    .badge-foto { background-color: #D1C8BA; color: #4A453F; padding: 3px 10px; border-radius: 12px; font-size: 0.65rem; font-weight: 600; letter-spacing: 0.5px; margin-right: 8px; }
    .badge-keyword { background-color: #FFFFFF; color: #7B7163; border: 1px solid #D1C8BA; padding: 4px 12px; border-radius: 16px; font-size: 0.75rem; font-weight: 500; margin: 0 5px 5px 0; display: inline-block; }
</style>
"""
st.markdown(estilo_editorial, unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 style='text-align: left;'>itsbgart <span style='font-family: Montserrat; font-size: 1.3rem; color: #A39B8F; font-weight:300; letter-spacing:1px;'> | CUADRO DE MANDOS</span></h1>", unsafe_allow_html=True)

# --- EXTRACCIÓN DE DATOS (CON CACHÉ) ---
@st.cache_data(ttl=3600) # Los datos se guardan en la memoria RAM durante 1 hora (3600 segundos)
def cargar_datos_panel():
    conexion = obtener_conexion()
    if conexion:
        query_metricas = """
            SELECT c.plataforma, c.estilo_visual, c.titulo, c.fecha_publicacion, 
                   MAX(m.visualizaciones) as visualizaciones, MAX(m.likes) as likes
            FROM contenidos c
            JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
            GROUP BY c.id_contenido, c.plataforma, c.estilo_visual, c.titulo, c.fecha_publicacion
        """
        df_m = pd.read_sql(query_metricas, conexion)
        
        query_ia = "SELECT analisis_rendimiento, ideas_contenido FROM insights_ia ORDER BY id_insight DESC LIMIT 1"
        df_i = pd.read_sql(query_ia, conexion)
        conexion.close()
        return df_m, df_i
    return pd.DataFrame(), pd.DataFrame()

# Llamamos a la función cacheada
df_metricas, df_ia = cargar_datos_panel()

if df_metricas.empty:
    st.error("Error al conectar con la base de datos o sin datos disponibles.")
    st.stop()

# --- FUNCIONES AUXILIARES ---
def generar_linea_arte(datos, color):
    df_agrupado = datos.groupby('fecha_publicacion')['visualizaciones'].sum().reset_index()
    return alt.Chart(df_agrupado).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X('fecha_publicacion:T', title='', axis=alt.Axis(grid=False, labelColor='#A39B8F')),
        y=alt.Y('visualizaciones:Q', title='', axis=alt.Axis(gridColor='#E8E3DA', labelColor='#A39B8F')),
        tooltip=['fecha_publicacion', 'visualizaciones']
    ).properties(height=280).configure_view(strokeWidth=0).configure(background='#FDFBF7').configure_line(color=color).configure_point(color=color, size=60)

def renderizar_etiquetas_visuales(texto):
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
    
def extraer_palabras_clave(df, top_n=5):
    if df.empty: return []
    stop_words = {"el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "pero", "si", "por", "para", "como", "en", "de", "a", "con", "sin", "mi", "tu", "su", "mis", "tus", "sus", "que", "qué", "al", "del", "lo", "se", "me", "te", "es", "vlog", "video", "vídeo", "cómo", "una"}
    texto_completo = " ".join(df['titulo'].dropna().tolist()).lower()
    palabras = re.findall(r'\b[a-záéíóúñ]{3,}\b', texto_completo)
    palabras_limpias = [p for p in palabras if p not in stop_words]
    contador = Counter(palabras_limpias)
    return [palabra for palabra, frec in contador.most_common(top_n)]

# --- PARSEO DE IA (ACTUALIZADO PARA INSTAGRAM) ---
ideas_yt, ideas_tt, ideas_ig = "Generando ideas...", "Generando ideas...", "Generando ideas..."
if not df_ia.empty:
    analisis_global = df_ia.iloc[0]['analisis_rendimiento']
    ideas_raw = df_ia.iloc[0]['ideas_contenido']
    
    match_yt = re.search(r'\[YOUTUBE\](.*?)\[TIKTOK\]', ideas_raw, re.DOTALL)
    match_tt = re.search(r'\[TIKTOK\](.*?)\[INSTAGRAM\]', ideas_raw, re.DOTALL)
    match_ig = re.search(r'\[INSTAGRAM\](.*)', ideas_raw, re.DOTALL)
    
    if match_yt: ideas_yt = match_yt.group(1).strip()
    if match_tt: ideas_tt = match_tt.group(1).strip()
    if match_ig: ideas_ig = match_ig.group(1).strip()

# --- RENDERIZADO PRINCIPAL ---
if not df_metricas.empty:
    df_metricas['visualizaciones'] = df_metricas['visualizaciones'].fillna(0).astype(int)
    df_metricas['likes'] = df_metricas['likes'].fillna(0).astype(int)
    df_metricas['estilo_visual'] = df_metricas['estilo_visual'].fillna('Vídeo')
    df_metricas['fecha_publicacion'] = pd.to_datetime(df_metricas['fecha_publicacion'])
    df_metricas['engagement_pct'] = (df_metricas['likes'] / df_metricas['visualizaciones'] * 100).fillna(0)

    # --- BARRA DE CONTROLES (Integrada) ---
    st.markdown("<hr style='border: 0; height: 1px; background: #E8E3DA; margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
    
    col_filtro_tiempo, col_filtro_texto = st.columns([2, 1])

    with col_filtro_tiempo:
        st.markdown("<p style='font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F; font-weight:600; margin-bottom:5px;'>📅 Filtrar por Fecha</p>", unsafe_allow_html=True)
        opcion_tiempo = st.radio(
            "Tiempo",
            ("Todo el histórico", "Últimos 30 días", "Últimos 7 días"),
            horizontal=True,
            label_visibility="collapsed"
        )

    with col_filtro_texto:
        st.markdown("<p style='font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F; font-weight:600; margin-bottom:5px;'>🔍 Buscar Obra Específica</p>", unsafe_allow_html=True)
        busqueda = st.text_input("Buscar", placeholder="Ej. vlog, pintura, marruecos...", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- LÓGICA DE LOS FILTROS ---
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
        st.warning("No hay resultados para los filtros seleccionados. Intenta ampliar la búsqueda.")
        st.stop()

    # --- KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    total_vistas = df_filtrado['visualizaciones'].sum()
    total_likes = df_filtrado['likes'].sum()
    engagement_medio = df_filtrado['engagement_pct'].mean()
    
    col1.metric("Exposición (Vistas)", f"{total_vistas:,}".replace(',', '.'))
    col2.metric("Interacciones (Likes)", f"{total_likes:,}".replace(',', '.'))
    col3.metric("Obras en Periodo", len(df_filtrado['titulo'].unique()))
    col4.metric("Engagement Promedio", f"{engagement_medio:.2f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # ✂️ AQUÍ EMPIEZA EL CÓDIGO NUEVO (SÚPER-ECOSISTEMA)
    # ==========================================
    
    # --- 1. MÓDULO DE INTELIGENCIA ARTIFICIAL GLOBAL ---
    st.markdown("### 🧠 Insights y Recomendaciones de IA")

    if not df_ia.empty:
        caja_ia1, caja_ia2 = st.columns(2)
        with caja_ia1:
            st.info("**Lectura del Rendimiento:**\n\n" + analisis_global)
    else:
        st.info("La IA está analizando los datos. Aún no hay recomendaciones disponibles.")

    st.markdown("<hr style='border: 1px solid #EAE6DF;'>", unsafe_allow_html=True)

    # --- 2. ECOSISTEMA VISUAL INTERACTIVO ---
    st.markdown("### 📊 Rendimiento del Ecosistema")

    col_grafico1, col_grafico2 = st.columns([2, 1])

    with col_grafico1:
        st.markdown("**Evolución de Visualizaciones por Plataforma**")
        grafico_lineas = alt.Chart(df_filtrado).mark_line(point=True).encode(
            x=alt.X('fecha_publicacion:T', title='Fecha de Publicación'),
            y=alt.Y('visualizaciones:Q', title='Visualizaciones'),
            color=alt.Color('plataforma:N', scale=alt.Scale(scheme='set2'), title='Plataforma'),
            tooltip=['titulo', 'plataforma', 'fecha_publicacion', 'visualizaciones', 'likes']
        ).properties(height=350).interactive()
        st.altair_chart(grafico_lineas, use_container_width=True)

    with col_grafico2:
        st.markdown("**Interacciones por Estilo Visual**")
        grafico_barras = alt.Chart(df_filtrado).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X('estilo_visual:N', title='Línea Editorial', sort='-y'),
            y=alt.Y('sum(likes):Q', title='Total de Likes'),
            color=alt.Color('estilo_visual:N', legend=None, scale=alt.Scale(scheme='pastel1')),
            tooltip=['estilo_visual', 'sum(likes)']
        ).properties(height=350)
        st.altair_chart(grafico_barras, use_container_width=True)

    with st.expander("Ver tabla de datos original"):
        st.dataframe(df_filtrado[['fecha_publicacion', 'titulo', 'plataforma', 'estilo_visual', 'visualizaciones', 'likes']].sort_values('fecha_publicacion', ascending=False), use_container_width=True)

    # ==========================================
    # ✂️ AQUÍ TERMINA EL CÓDIGO NUEVO
    # ==========================================

    # --- PESTAÑAS (Mantenidas de tu código original) ---
    tab_global, tab_yt, tab_tt, tab_ig = st.tabs(["Línea Temporal", "YouTube", "TikTok", "Instagram"])
    
    with tab_global:
        st.markdown("<h3 style='font-size:1.2rem; margin-bottom:1rem;'>Evolución del Rendimiento</h3>", unsafe_allow_html=True)
        st.altair_chart(generar_linea_arte(df_filtrado, '#7B7163'), use_container_width=True)

    with tab_yt:
        df_yt = df_filtrado[df_filtrado['plataforma'] == 'youtube']
        col_datos, col_estrategia = st.columns([3, 2], gap="large")
        
        with col_datos:
            st.markdown("<h3 style='font-size:1.2rem;'>Histórico Profundo</h3>", unsafe_allow_html=True)
            if not df_yt.empty:
                st.altair_chart(generar_linea_arte(df_yt, '#8C8273'), use_container_width=True)
                
                df_tabla_yt = df_yt[['titulo', 'estilo_visual', 'fecha_publicacion', 'visualizaciones', 'engagement_pct']].copy()
                df_tabla_yt['fecha_publicacion'] = df_tabla_yt['fecha_publicacion'].dt.strftime('%Y-%m-%d')
                df_tabla_yt['engagement_pct'] = df_tabla_yt['engagement_pct'].apply(lambda x: f"{x:.2f}%")
                st.dataframe(df_tabla_yt.rename(columns={'estilo_visual': 'Formato', 'titulo': 'Obra', 'fecha_publicacion': 'Fecha', 'engagement_pct': 'Ratio Likes'}), width='stretch', hide_index=True)
            else:
                st.info("Sin registros en este periodo.")
                
        with col_estrategia:
            claves_yt = extraer_palabras_clave(df_yt)
            if claves_yt:
                st.markdown("<p style='font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F; font-weight:600; margin-bottom: 5px;'>🔍 Palabras de Retención</p>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='badge-keyword'>#{palabra}</span>" for palabra in claves_yt]), unsafe_allow_html=True)

            st.markdown("<h3 style='font-size:1.2rem; color:#8C8273; margin-top:1rem;'>💡 Dirección Creativa YouTube</h3>", unsafe_allow_html=True)
            st.markdown(f"<div class='idea-card' style='font-size:0.9rem; line-height:1.6;'>{renderizar_etiquetas_visuales(ideas_yt)}</div>", unsafe_allow_html=True)

    with tab_tt:
        df_tt = df_filtrado[df_filtrado['plataforma'] == 'tiktok']
        col_datos_tt, col_estrategia_tt = st.columns([3, 2], gap="large")
        
        with col_datos_tt:
            st.markdown("<h3 style='font-size:1.2rem;'>Histórico Viral</h3>", unsafe_allow_html=True)
            if not df_tt.empty:
                st.altair_chart(generar_linea_arte(df_tt, '#5C554B'), use_container_width=True)
                
                df_tabla_tt = df_tt[['titulo', 'estilo_visual', 'fecha_publicacion', 'visualizaciones', 'engagement_pct']].copy()
                df_tabla_tt['fecha_publicacion'] = df_tabla_tt['fecha_publicacion'].dt.strftime('%Y-%m-%d')
                df_tabla_tt['engagement_pct'] = df_tabla_tt['engagement_pct'].apply(lambda x: f"{x:.2f}%")
                st.dataframe(df_tabla_tt.rename(columns={'estilo_visual': 'Formato', 'titulo': 'Obra', 'fecha_publicacion': 'Fecha', 'engagement_pct': 'Ratio Likes'}), width='stretch', hide_index=True)
            else:
                st.info("Sin registros en este periodo.")
                
        with col_estrategia_tt:
            claves_tt = extraer_palabras_clave(df_tt)
            if claves_tt:
                st.markdown("<p style='font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F; font-weight:600; margin-bottom: 5px;'>🎯 Ganchos de Clasificación</p>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='badge-keyword'>#{palabra}</span>" for palabra in claves_tt]), unsafe_allow_html=True)

            st.markdown("<h3 style='font-size:1.2rem; color:#8C8273; margin-top:1rem;'>💡 Dirección Creativa TikTok</h3>", unsafe_allow_html=True)
            st.markdown(f"<div class='idea-card' style='font-size:0.9rem; line-height:1.6;'>{renderizar_etiquetas_visuales(ideas_tt)}</div>", unsafe_allow_html=True)

    with tab_ig:
        query_ig_ampliado = """
            SELECT c.titulo, c.estilo_visual, c.fecha_publicacion, 
                   MAX(m.visualizaciones) as vistas, MAX(m.likes) as likes, 
                   MAX(m.compartidos) as compartidos, MAX(m.guardados) as guardados
            FROM contenidos c
            JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
            WHERE c.plataforma = 'instagram'
            GROUP BY c.id_contenido, c.estilo_visual, c.titulo, c.fecha_publicacion
        """
        try:
            con_ig = obtener_conexion()
            df_ig_avanzado = pd.read_sql(query_ig_ampliado, con_ig)
            con_ig.close()
            df_ig_avanzado['fecha_publicacion'] = pd.to_datetime(df_ig_avanzado['fecha_publicacion'])
            if opcion_tiempo == "Últimos 30 días":
                df_ig_avanzado = df_ig_avanzado[df_ig_avanzado['fecha_publicacion'] >= fecha_limite]
            elif opcion_tiempo == "Últimos 7 días":
                df_ig_avanzado = df_ig_avanzado[df_ig_avanzado['fecha_publicacion'] >= fecha_limite]
            if busqueda:
                df_ig_avanzado = df_ig_avanzado[df_ig_avanzado['titulo'].str.contains(busqueda, case=False, na=False)]
        except:
            df_ig_avanzado = pd.DataFrame()

        col_datos_ig, col_estrategia_ig = st.columns([3, 2], gap="large")
        
        with col_datos_ig:
            st.markdown("<h3 style='font-size:1.2rem;'>Métricas de Valor Estético</h3>", unsafe_allow_html=True)
            if not df_ig_avanzado.empty:
                st.altair_chart(generar_linea_arte(df_ig_avanzado.rename(columns={'vistas':'visualizaciones'}), '#D1C8BA'), use_container_width=True)
                
                df_tabla_ig = df_ig_avanzado[['titulo', 'estilo_visual', 'fecha_publicacion', 'likes', 'compartidos', 'guardados']].copy()
                df_tabla_ig['fecha_publicacion'] = df_tabla_ig['fecha_publicacion'].dt.strftime('%Y-%m-%d')
                
                st.dataframe(df_tabla_ig.rename(columns={
                    'estilo_visual': 'Formato', 
                    'titulo': 'Obra', 
                    'fecha_publicacion': 'Fecha',
                    'likes': '❤️',
                    'compartidos': '✈️',
                    'guardados': '💾'
                }), width='stretch', hide_index=True)
            else:
                st.info("Sin registros de Instagram para este periodo.")
                
        with col_estrategia_ig:
            claves_ig = extraer_palabras_clave(df_ig_avanzado.rename(columns={'vistas':'visualizaciones'}))
            if claves_ig:
                st.markdown("<p style='font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#A39B8F; font-weight:600; margin-bottom: 5px;'>✨ Conceptos Visuales Clave</p>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='badge-keyword'>#{palabra}</span>" for palabra in claves_ig]), unsafe_allow_html=True)

            st.markdown("<h3 style='font-size:1.2rem; color:#8C8273; margin-top:1rem;'>💡 Dirección Creativa Instagram</h3>", unsafe_allow_html=True)
            st.markdown(f"<div class='idea-card' style='font-size:0.9rem; line-height:1.6;'>{renderizar_etiquetas_visuales(ideas_ig)}</div>", unsafe_allow_html=True)
else:
    st.warning("Ejecuta los extractores para poblar el panel.")