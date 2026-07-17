"""
Histórico de ideas ejecutadas — Feedback loop para la IA.

Permite a la artista marcar qué ideas publicó, asociarlas a posts reales,
y alimenta el contexto de la IA para que aprenda de los resultados.
"""

import re
import streamlit as st
import pandas as pd
from datetime import datetime
from conexion import obtener_conexion


def _parsear_ideas_de_insight(ideas_raw, plataforma_filtro=None):
    """Extrae ideas individuales del texto generado por la IA."""
    ideas = []
    if not ideas_raw:
        return ideas

    texto = str(ideas_raw)

    # Tags de formato que indican el inicio de una idea
    tags_formato = {
        '[VIDEO LARGO]': ('youtube', 'Vídeo largo'),
        '[SHORT]': ('youtube', 'Short'),
        '[TIKTOK VERTICAL]': ('tiktok', 'Vídeo vertical'),
        '[REEL]': ('instagram', 'Reel'),
        '[CARRUSEL]': ('instagram', 'Carrusel'),
        '[STORY]': ('instagram', 'Story'),
    }

    for tag, (plataforma, formato) in tags_formato.items():
        if plataforma_filtro and plataforma != plataforma_filtro:
            continue

        partes = texto.split(tag)
        for i in range(1, len(partes)):
            # Extraer el título de la idea (primera línea tras el tag)
            bloque = partes[i].strip()
            primera_linea = bloque.split('\n')[0].strip()
            # Limpiar el título
            titulo = primera_linea.strip('- ').strip()
            if titulo and len(titulo) > 5:
                ideas.append({
                    'plataforma': plataforma,
                    'formato': formato,
                    'texto': f"{tag} {titulo}",
                    'titulo_corto': titulo[:80]
                })

    return ideas


def _guardar_ideas_desde_insight(id_insight, ideas_raw):
    """Parsea y guarda las ideas individuales de un insight en la BD."""
    conexion = obtener_conexion()
    if not conexion:
        return 0

    ideas = _parsear_ideas_de_insight(ideas_raw)
    if not ideas:
        return 0

    try:
        cursor = conexion.cursor()
        guardadas = 0
        for idea in ideas:
            # Verificar que no existe ya (evitar duplicados)
            cursor.execute(
                "SELECT COUNT(*) FROM ideas_ejecutadas WHERE id_insight = %s AND texto_idea = %s",
                (id_insight, idea['texto'][:500])
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO ideas_ejecutadas (id_insight, plataforma, formato, texto_idea)
                    VALUES (%s, %s, %s, %s)
                """, (id_insight, idea['plataforma'], idea['formato'], idea['texto'][:500]))
                guardadas += 1

        conexion.commit()
        cursor.close()
        conexion.close()
        return guardadas
    except Exception:
        conexion.close()
        return 0


def _marcar_ejecutada(id_idea, id_contenido=None):
    """Marca una idea como ejecutada y opcionalmente la enlaza a un post."""
    conexion = obtener_conexion()
    if not conexion:
        return False
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE ideas_ejecutadas 
            SET ejecutada = TRUE, fecha_marcada = %s, id_contenido = %s
            WHERE id = %s
        """, (datetime.now(), id_contenido, id_idea))
        conexion.commit()
        cursor.close()
        conexion.close()
        return True
    except Exception:
        conexion.close()
        return False


def _desmarcar_idea(id_idea):
    """Desmarca una idea como no ejecutada."""
    conexion = obtener_conexion()
    if not conexion:
        return False
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE ideas_ejecutadas 
            SET ejecutada = FALSE, fecha_marcada = NULL, id_contenido = NULL
            WHERE id = %s
        """, (id_idea,))
        conexion.commit()
        cursor.close()
        conexion.close()
        return True
    except Exception:
        conexion.close()
        return False


def cargar_ideas_con_resultados():
    """Carga ideas ejecutadas con sus métricas reales (para el feedback loop de la IA)."""
    conexion = obtener_conexion()
    if not conexion:
        return pd.DataFrame()

    try:
        df = pd.read_sql("""
            SELECT ie.plataforma, ie.formato, ie.texto_idea, ie.ejecutada,
                   m.visualizaciones, m.likes, m.compartidos, m.guardados
            FROM ideas_ejecutadas ie
            LEFT JOIN metricas_rendimiento m ON ie.id_contenido = m.id_contenido
            WHERE ie.fecha_generacion >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            ORDER BY ie.fecha_generacion DESC
        """, conexion)
        conexion.close()
        return df
    except Exception:
        conexion.close()
        return pd.DataFrame()


def construir_contexto_feedback():
    """Construye el bloque de texto de feedback para inyectar en el prompt de la IA."""
    df = cargar_ideas_con_resultados()
    if df.empty:
        return ""

    ejecutadas = df[df['ejecutada'] == True]
    no_ejecutadas = df[df['ejecutada'] == False]

    if ejecutadas.empty:
        return ""

    contexto = "\n\n📋 FEEDBACK DE IDEAS ANTERIORES (lo que la artista ejecutó y su resultado):\n"

    # Ideas ejecutadas con resultado
    for _, row in ejecutadas.iterrows():
        vistas = int(row['visualizaciones']) if pd.notna(row['visualizaciones']) else 0
        likes = int(row['likes']) if pd.notna(row['likes']) else 0
        guardados = int(row['guardados']) if pd.notna(row['guardados']) else 0

        # Determinar si fue éxito
        engagement = likes / max(vistas, 1) * 100
        if engagement > 5 or guardados > 20:
            resultado = "✅ ÉXITO"
        elif engagement > 2:
            resultado = "👍 ACEPTABLE"
        else:
            resultado = "⚠️ BAJO RENDIMIENTO"

        idea_corta = row['texto_idea'][:60]
        contexto += f"  - [{row['plataforma'].upper()}] '{idea_corta}' → {resultado} ({vistas} vistas, {engagement:.1f}% eng, {guardados} guardados)\n"

    # Ideas no ejecutadas (la artista las ignoró → la IA debería generar menos de ese tipo)
    if len(no_ejecutadas) > 3:
        contexto += f"\n  ⚠️ {len(no_ejecutadas)} ideas NO fueron ejecutadas por la artista. "
        contexto += "Genera ideas más alineadas con las que SÍ ejecuta (proceso creativo, ASMR, viajes).\n"

    return contexto


def renderizar_ideas_ejecutadas(df_ia, plataforma=None):
    """Renderiza la sección de ideas ejecutadas con diseño de tarjetas y botones."""

    st.markdown("#### 📋 Ideas de la IA → ¿Las publicaste?")
    st.markdown("<p style='font-size:0.8rem; color:#A39B8F;'>Esto ayuda a la IA a aprender qué tipo de ideas te funcionan mejor.</p>", unsafe_allow_html=True)

    # Asegurar que las ideas del último insight estén guardadas en la BD
    if not df_ia.empty:
        try:
            conexion = obtener_conexion()
            if conexion:
                cursor = conexion.cursor(dictionary=True)
                cursor.execute("SELECT id_insight FROM insights_ia ORDER BY fecha_generacion DESC LIMIT 1")
                ultimo = cursor.fetchone()
                cursor.close()
                conexion.close()

                if ultimo:
                    ideas_raw = df_ia.iloc[0].get('ideas_contenido', '')
                    _guardar_ideas_desde_insight(ultimo['id_insight'], ideas_raw)
        except Exception:
            pass

    # Cargar ideas de la BD
    conexion = obtener_conexion()
    if not conexion:
        st.caption("No se pudo conectar a la BD.")
        return

    try:
        query = """
            SELECT ie.id, ie.plataforma, ie.formato, ie.texto_idea, ie.ejecutada, 
                   ie.id_contenido, ie.fecha_generacion,
                   m.visualizaciones, m.likes, m.guardados
            FROM ideas_ejecutadas ie
            LEFT JOIN metricas_rendimiento m ON ie.id_contenido = m.id_contenido
            WHERE ie.fecha_generacion >= DATE_SUB(CURDATE(), INTERVAL 21 DAY)
        """
        if plataforma:
            query += f" AND ie.plataforma = '{plataforma}'"
        query += " ORDER BY ie.fecha_generacion DESC, ie.id DESC"

        df_ideas = pd.read_sql(query, conexion)
        conexion.close()
    except Exception:
        conexion.close()
        st.caption("Tabla de ideas no disponible. Ejecuta `migracion_ideas_ejecutadas.sql` en phpMyAdmin.")
        return

    if df_ideas.empty:
        st.caption("Sincroniza con la IA para generar ideas que puedas marcar.")
        return

    # Cargar posts recientes para asociar
    conexion2 = obtener_conexion()
    posts_recientes = {}
    if conexion2:
        try:
            q_posts = "SELECT id_contenido, titulo, plataforma FROM contenidos WHERE fecha_publicacion >= DATE_SUB(CURDATE(), INTERVAL 21 DAY) ORDER BY fecha_publicacion DESC"
            df_posts = pd.read_sql(q_posts, conexion2)
            conexion2.close()
            for plat in df_posts['plataforma'].unique():
                posts_recientes[plat] = df_posts[df_posts['plataforma'] == plat][['id_contenido', 'titulo']].to_dict('records')
        except Exception:
            conexion2.close()

    # Estadísticas rápidas
    total = len(df_ideas)
    ejecutadas = len(df_ideas[df_ideas['ejecutada'] == True])
    no_marcadas = len(df_ideas[df_ideas['ejecutada'] == False])

    # Barra de progreso visual
    tasa = ejecutadas / max(total, 1)
    st.markdown(f"""
    <div style="margin-bottom:1rem;">
        <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#7B7163; margin-bottom:4px;">
            <span>✅ {ejecutadas} publicadas</span>
            <span>○ {no_marcadas} pendientes</span>
        </div>
        <div style="background:#F4F1EA; border-radius:6px; height:8px; overflow:hidden;">
            <div style="background: linear-gradient(90deg, #5C554B, #8C8273); width:{tasa*100}%; height:100%; border-radius:6px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Renderizar cada idea como tarjeta con botones
    for _, idea in df_ideas.iterrows():
        id_idea = int(idea['id'])
        plat = idea['plataforma']
        esta_ejecutada = bool(idea['ejecutada'])
        formato = idea.get('formato', '')

        emoji_plat = {'instagram': '📸', 'tiktok': '🎵', 'youtube': '📺'}.get(plat, '📊')
        emoji_fmt = {'Reel': '🎬', 'Carrusel': '🖼️', 'Story': '🤳', 'Vídeo vertical': '📱', 'Vídeo largo': '▶', 'Short': '📱'}.get(formato, '📌')

        # Limpiar texto de la idea (quitar tags de formato)
        texto_limpio = re.sub(r'\[[^\]]+\]\s*', '', idea['texto_idea']).strip()
        texto_corto = texto_limpio[:70]

        # Estado y resultado
        if esta_ejecutada:
            # Tarjeta con resultado
            resultado_texto = ""
            if pd.notna(idea.get('visualizaciones')):
                vistas = int(idea['visualizaciones'])
                likes = int(idea['likes']) if pd.notna(idea['likes']) else 0
                eng = likes / max(vistas, 1) * 100
                resultado_texto = f"{vistas:,} vistas · {eng:.1f}% eng"

            st.markdown(f"""
            <div style="background:#F8FBF8; border:1px solid #C8E6C9; border-radius:10px; padding:0.8rem 1rem; margin-bottom:0.5rem; display:flex; align-items:center; gap:12px;">
                <div style="font-size:1.2rem;">✅</div>
                <div style="flex:1;">
                    <p style="margin:0; font-size:0.8rem; color:#4A453F; font-weight:500;">{texto_corto}</p>
                    <p style="margin:2px 0 0; font-size:0.68rem; color:#7B7163;">{emoji_fmt} {formato} {'· ' + resultado_texto if resultado_texto else ''}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Botón para desmarcar (discreto)
            if st.button("↩ Desmarcar", key=f"desmarcar_{id_idea}", type="secondary"):
                _desmarcar_idea(id_idea)
                st.rerun()

        else:
            # Tarjeta pendiente con botones de acción
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E8E3DA; border-radius:10px; padding:0.8rem 1rem; margin-bottom:0.4rem;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="font-size:1rem;">{emoji_fmt}</div>
                    <div style="flex:1;">
                        <p style="margin:0; font-size:0.8rem; color:#4A453F; font-weight:500;">{texto_corto}</p>
                        <p style="margin:2px 0 0; font-size:0.65rem; color:#A39B8F;">{emoji_plat} {plat.capitalize()} · {formato}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_pub, col_desc, col_space = st.columns([1, 1, 2])
            with col_pub:
                if st.button("✅ Publicada", key=f"pub_{id_idea}", type="secondary"):
                    posts_plat = posts_recientes.get(plat, [])
                    id_contenido_asociar = posts_plat[0]['id_contenido'] if posts_plat else None
                    _marcar_ejecutada(id_idea, id_contenido_asociar)
                    st.rerun()
            with col_desc:
                if st.button("🗑️ Descartada", key=f"desc_{id_idea}", type="secondary"):
                    _marcar_ejecutada(id_idea, None)  # Marcada pero sin post → la IA sabe que se intentó
                    st.rerun()
