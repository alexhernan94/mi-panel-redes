import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion
from utils import get_logger

logger = get_logger('motor_ia')
load_dotenv()

# --- 📊 EXTRACCIÓN INTELIGENTE DE DATOS ---
def extraer_datos_rendimiento(cursor):
    """Extrae datos multi-dimensionales para alimentar el análisis de la IA."""
    
    datos = {}
    
    # 1. Top 10 publicaciones globales (por engagement combinado)
    cursor.execute("""
        SELECT c.plataforma, c.titulo, c.estilo_visual,
               MAX(m.visualizaciones) as vistas,
               MAX(m.likes) as likes,
               MAX(m.compartidos) as compartidos,
               MAX(m.guardados) as guardados
        FROM contenidos c
        JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
        GROUP BY c.id_contenido, c.plataforma, c.titulo, c.estilo_visual
        ORDER BY (MAX(m.likes) + MAX(m.compartidos) * 3 + MAX(m.guardados) * 5) DESC
        LIMIT 10
    """)
    datos['top_engagement'] = cursor.fetchall()
    
    # 2. Top 5 por viralidad (compartidos + guardados relativos a vistas)
    cursor.execute("""
        SELECT c.plataforma, c.titulo, c.estilo_visual,
               MAX(m.visualizaciones) as vistas,
               MAX(m.compartidos) as compartidos,
               MAX(m.guardados) as guardados
        FROM contenidos c
        JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
        WHERE m.visualizaciones > 100
        GROUP BY c.id_contenido, c.plataforma, c.titulo, c.estilo_visual
        ORDER BY (MAX(m.compartidos) + MAX(m.guardados)) DESC
        LIMIT 5
    """)
    datos['top_viral'] = cursor.fetchall()
    
    # 3. Rendimiento medio por categoría (estilo_visual)
    cursor.execute("""
        SELECT c.estilo_visual,
               COUNT(*) as total_posts,
               ROUND(AVG(m.visualizaciones)) as media_vistas,
               ROUND(AVG(m.likes)) as media_likes,
               ROUND(AVG(m.compartidos)) as media_compartidos,
               ROUND(AVG(m.guardados)) as media_guardados
        FROM contenidos c
        JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
        GROUP BY c.estilo_visual
        HAVING total_posts >= 3
        ORDER BY media_guardados DESC
    """)
    datos['rendimiento_por_categoria'] = cursor.fetchall()
    
    # 4. Rendimiento por plataforma
    cursor.execute("""
        SELECT c.plataforma,
               COUNT(*) as total_posts,
               ROUND(AVG(m.visualizaciones)) as media_vistas,
               ROUND(AVG(m.likes)) as media_likes,
               ROUND(AVG(m.compartidos)) as media_compartidos,
               ROUND(AVG(m.guardados)) as media_guardados
        FROM contenidos c
        JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
        GROUP BY c.plataforma
        ORDER BY media_vistas DESC
    """)
    datos['rendimiento_por_plataforma'] = cursor.fetchall()
    
    # 5. Contenido reciente (últimos 30 días) para detectar tendencias actuales
    cursor.execute("""
        SELECT c.plataforma, c.titulo, c.estilo_visual,
               MAX(m.visualizaciones) as vistas,
               MAX(m.likes) as likes,
               MAX(m.guardados) as guardados
        FROM contenidos c
        JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
        WHERE c.fecha_publicacion >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY c.id_contenido, c.plataforma, c.titulo, c.estilo_visual
        ORDER BY vistas DESC
        LIMIT 10
    """)
    datos['recientes'] = cursor.fetchall()
    
    return datos


# --- 🧠 CONSTRUCCIÓN DEL CONTEXTO PARA LA IA ---
def construir_contexto(datos):
    """Transforma los datos extraídos en un bloque de texto contextual para el prompt."""
    
    contexto = ""
    
    # Top engagement
    if datos['top_engagement']:
        contexto += "📈 TOP 10 PUBLICACIONES POR ENGAGEMENT:\n"
        for ob in datos['top_engagement']:
            contexto += (
                f"  - [{ob['plataforma'].upper()}] '{ob['titulo'][:60]}' "
                f"({ob['estilo_visual']}) → Vistas: {ob['vistas']} | "
                f"Likes: {ob['likes']} | Compartidos: {ob['compartidos']} | "
                f"Guardados: {ob['guardados']}\n"
            )
        contexto += "\n"
    
    # Top viral
    if datos['top_viral']:
        contexto += "🔥 TOP 5 MÁS VIRALES (compartidos + guardados):\n"
        for ob in datos['top_viral']:
            contexto += (
                f"  - [{ob['plataforma'].upper()}] '{ob['titulo'][:60]}' "
                f"({ob['estilo_visual']}) → Compartidos: {ob['compartidos']} | "
                f"Guardados: {ob['guardados']}\n"
            )
        contexto += "\n"
    
    # Rendimiento por categoría
    if datos['rendimiento_por_categoria']:
        contexto += "📊 RENDIMIENTO MEDIO POR CATEGORÍA:\n"
        for cat in datos['rendimiento_por_categoria']:
            contexto += (
                f"  - {cat['estilo_visual']:20s} ({cat['total_posts']:3d} posts) → "
                f"Vistas: {cat['media_vistas']} | Likes: {cat['media_likes']} | "
                f"Compartidos: {cat['media_compartidos']} | Guardados: {cat['media_guardados']}\n"
            )
        contexto += "\n"
    
    # Rendimiento por plataforma
    if datos['rendimiento_por_plataforma']:
        contexto += "🌐 RENDIMIENTO MEDIO POR PLATAFORMA:\n"
        for plat in datos['rendimiento_por_plataforma']:
            contexto += (
                f"  - {plat['plataforma'].upper():10s} ({plat['total_posts']:3d} posts) → "
                f"Vistas: {plat['media_vistas']} | Likes: {plat['media_likes']} | "
                f"Guardados: {plat['media_guardados']}\n"
            )
        contexto += "\n"
    
    # Tendencias recientes
    if datos['recientes']:
        contexto += "🕐 TENDENCIAS RECIENTES (últimos 30 días):\n"
        for ob in datos['recientes']:
            contexto += (
                f"  - [{ob['plataforma'].upper()}] '{ob['titulo'][:60]}' "
                f"({ob['estilo_visual']}) → Vistas: {ob['vistas']}\n"
            )
    
    return contexto


# --- 💡 PROMPT PRINCIPAL ---
# --- 💡 PROMPT PRINCIPAL ---
def construir_prompt(datos_contexto):
    """Genera el prompt optimizado para Gemini basado en los datos reales."""
    
    return f"""
Actúa como un director creativo y estratega experto en crecimiento orgánico de canales de YouTube, TikTok e Instagram.
Estás trabajando para la marca 'itsbgart', una artista e ilustradora que:
- Hace papel reciclado artesanal y sobre él imprime sus ilustraciones.
- Hace encargos personalizados en acuarela (retratos, recuerdos de viajes).
- Comparte su proceso creativo, vlogs de su vida como artista y viajes.
- Su audiencia valora la autenticidad, la calma, lo artesanal y la conexión emocional.

MÉTRICAS CLAVE DE RENDIMIENTO HISTÓRICO DE LA ARTISTA:

{datos_contexto}

ANÁLISIS REQUERIDO Y TENDENCIAS ACTUALES:
1. Analiza los GUARDADOS y COMPARTIDOS del histórico de la artista.
2. CRUZA esta información con las TENDENCIAS ACTUALES GLOBALES de cada plataforma para creadores de arte y estilo de vida (qué tipo de ASMR funciona, duraciones óptimas, transiciones estéticas, narrativas de vlogs, etc.).
3. Genera ideas que fusionen lo que a ella le funciona con lo que el algoritmo está premiando ahora mismo.

REGLAS ESTRICTAS DE FORMATO: 
1. NO uses negritas (asteriscos dobles **) en las etiquetas de formato. Escribe exactamente [VIDEO LARGO], [SHORT], [TIKTOK VERTICAL], [REEL], [STORY] o [CARRUSEL].
2. Respeta escrupulosamente los saltos de línea. Cada viñeta (-) debe ir en una línea nueva.
3. Cada idea debe ser concreta y ejecutable, no genérica.
4. Adapta las ideas al estilo real de la artista (papel reciclado, acuarela, naturaleza, slow living).

Estructura el output EXACTAMENTE así:

[TENDENCIAS]
(Párrafo resumen en viñetas con las tendencias globales de esta semana en los algoritmos de YouTube, TikTok e Instagram para creadores de arte, ilustración y slow living).

[ANALISIS]
(Párrafo de 4-5 líneas analizando qué elementos han funcionado históricamente y cómo se pueden potenciar con las tendencias actuales de las redes. Sé muy accionable).

[YOUTUBE]

[VIDEO LARGO] Título de la idea 1
- 👁️ Dirección de Arte: (Describe plano de cámara, iluminación o paleta cromática)
- 🎣 Gancho Narrativo: (El concepto de los primeros 5 segundos)
- 📐 Estructura: (Duración sugerida y arco narrativo)

[VIDEO LARGO] Título de la idea 2
- 👁️ Dirección de Arte: (Describe plano de cámara, iluminación o paleta cromática)
- 🎣 Gancho Narrativo: (El concepto de los primeros 5 segundos)
- 📐 Estructura: (Duración sugerida y arco narrativo)

[SHORT] Título de la idea 3
- 👁️ Dirección de Arte: (Estética del plano detalle)
- 🎣 Gancho Narrativo: (Estímulo visual inicial)

[SHORT] Título de la idea 4
- 👁️ Dirección de Arte: (Estética del plano detalle)
- 🎣 Gancho Narrativo: (Estímulo visual inicial)

[TIKTOK]

[TIKTOK VERTICAL] Título de la idea 1
- 👁️ Estímulo Visual: (Qué pasa en pantalla en el segundo 1 para retener)
- 🎵 Ritmo/Sonido: (Tipo de audio en tendencia, ASMR, música ambiente)
- 💡 Tendencia: (Explicación de por qué este formato funciona AHORA en TikTok)

[TIKTOK VERTICAL] Título de la idea 2
- 👁️ Estímulo Visual: (Qué pasa en pantalla en el segundo 1 para retener)
- 🎵 Ritmo/Sonido: (Tipo de audio en tendencia, ASMR, música ambiente)
- 💡 Tendencia: (Explicación de por qué este formato funciona AHORA en TikTok)

[TIKTOK VERTICAL] Título de la idea 3
- 👁️ Estímulo Visual: (Qué pasa en pantalla en el segundo 1 para retener)
- 🎵 Ritmo/Sonido: (Tipo de audio en tendencia, ASMR, música ambiente)
- 💡 Tendencia: (Explicación de por qué este formato funciona AHORA en TikTok)

[INSTAGRAM]

[REEL] Título de la idea 1
- 👁️ Estímulo Visual: (Transición o composición visual clave)
- 🎵 Ritmo/Sonido: (Audio estético sugerido o sonido tendencia)

[REEL] Título de la idea 2
- 👁️ Estímulo Visual: (Plano o secuencia visual principal)
- 🎵 Ritmo/Sonido: (Audio o sonido ambiente)

[CARRUSEL] Título de la idea 1
- 👁️ Flujo Visual: (Portada gancho -> desarrollo -> CTA final)
- 💬 Llamada a la acción: (Incentivo para que guarden, basado en el algoritmo actual)

[CARRUSEL] Título de la idea 2
- 👁️ Flujo Visual: (Secuencia visual entre slides)
- 💬 Llamada a la acción: (Incentivo para que compartan, basado en el algoritmo actual)

[STORY] Título de la idea 1
- 👁️ Interacción: (Sticker, encuesta o slider que use)
- 🎣 Gancho Visual: (Composición del frame)

[STORY] Título de la idea 2
- 👁️ Interacción: (Formato interactivo propuesto)
- 🎣 Gancho Visual: (Elemento visual clave)

[PLANIFICADOR SEMANAL]
Propón un calendario semanal concreto basado en los datos de rendimiento por día de la semana y formato. Estructura exactamente así:

- Lunes: (formato + plataforma + concepto breve)
- Martes: (formato + plataforma + concepto breve)
- Miércoles: (formato + plataforma + concepto breve)
- Jueves: (formato + plataforma + concepto breve)
- Viernes: (formato + plataforma + concepto breve)
- Sábado: (formato + plataforma + concepto breve)
- Domingo: (formato + plataforma + concepto breve)

Justifica brevemente por qué ese día va ese formato (basado en las métricas reales).

[CAPTIONS]
Genera 5 captions listos para copiar y pegar, optimizados para engagement (guardados + compartidos). Cada caption debe:
- Tener un gancho en la primera línea (lo que se ve antes del "más...")
- Incluir una llamada a la acción clara (guardar, compartir, comentar)
- Usar el tono de la artista (cercano, calmado, inspirador)
- Incluir 3-5 hashtags estratégicos del nicho arte/slow living
- Indicar para qué plataforma y formato es

Estructura:
1. [PLATAFORMA - FORMATO] Caption completo listo para usar
2. [PLATAFORMA - FORMATO] Caption completo listo para usar
3. [PLATAFORMA - FORMATO] Caption completo listo para usar
4. [PLATAFORMA - FORMATO] Caption completo listo para usar
5. [PLATAFORMA - FORMATO] Caption completo listo para usar
"""


# --- 🚀 FUNCIÓN PRINCIPAL ---
def analizar_y_generar_ideas():
    print("🧠 Motor IA — Iniciando análisis estratégico...")
    print("=" * 50)

    # 0. INICIALIZACIÓN DE GEMINI (A PRUEBA DE FALLOS)
    clave_api = os.getenv('GEMINI_API_KEY')
    
    # Si no la encuentra en el .env, intenta leerla de los secretos de Streamlit
    if not clave_api:
        try:
            import streamlit as st
            clave_api = st.secrets.get("GEMINI_API_KEY")
        except ImportError:
            pass

    if not clave_api:
        print("❌ Error: No se ha encontrado la clave de API de Gemini.")
        return

    # Inicializamos el cliente solo cuando la función es llamada
    cliente_ia = genai.Client(api_key=clave_api)
    
    # 1. CONEXIÓN A BASE DE DATOS
    conexion = obtener_conexion()
    if not conexion:
        print("❌ No se pudo conectar a la base de datos.")
        return

    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # 2. EXTRACCIÓN DE DATOS
        print("📥 Extrayendo datos de rendimiento...")
        datos = extraer_datos_rendimiento(cursor)
        
        if not datos['top_engagement']:
            print("⚠️ No hay suficientes datos en la base de datos para generar análisis.")
            return
        
        # 3. CONSTRUCCIÓN DEL CONTEXTO
        datos_contexto = construir_contexto(datos)
        print(f"📊 Datos procesados: {len(datos['top_engagement'])} top posts, "
              f"{len(datos['rendimiento_por_categoria'])} categorías analizadas.")
        
        # 4. GENERACIÓN CON IA
        prompt = construir_prompt(datos_contexto)
        
        respuesta = cliente_ia.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.9,
                top_p=0.95,
                max_output_tokens=5500,
            ),
        )
        
        texto_completo = respuesta.text
        
        if not texto_completo:
            print("❌ La IA no generó respuesta.")
            return
        
        # 5. SEGMENTACIÓN Y ALMACENAMIENTO
        tendencias, analisis, ideas_plataformas = segmentar_respuesta(texto_completo)

        sql_insert = """
            INSERT INTO insights_ia (tendencias_actuales, analisis_rendimiento, ideas_contenido) 
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql_insert, (tendencias, analisis, ideas_plataformas))
        
        # Mantener solo los últimos 10 registros para no crecer indefinidamente
        cursor.execute("""
            DELETE FROM insights_ia 
            WHERE id_insight NOT IN (
                SELECT id_insight FROM (
                    SELECT id_insight FROM insights_ia ORDER BY fecha_generacion DESC LIMIT 10
                ) AS recientes
            )
        """)
        
        conexion.commit()
        
        print("=" * 50)
        print("✅ Estrategia generada y guardada correctamente.")
        print(f"   → Análisis: {len(analisis)} caracteres")
        print(f"   → Ideas: {len(ideas_plataformas)} caracteres")

    except Exception as e:
        print(f"❌ Error en el motor de IA: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()


def segmentar_respuesta(texto):
    """Separa las tendencias, el análisis y las ideas de contenido de forma robusta."""
    tendencias = "Sin datos de tendencias."
    analisis = "Análisis no segmentado."
    ideas = texto
    
    # 1. Separamos las tendencias del resto
    if '[TENDENCIAS]' in texto and '[ANALISIS]' in texto:
        partes = texto.split('[ANALISIS]')
        tendencias = partes[0].replace('[TENDENCIAS]', '').strip()
        resto = '[ANALISIS]' + partes[1]
    else:
        resto = texto
        
    # 2. Separamos el análisis de las ideas, buscando la primera red que aparezca
    if '[YOUTUBE]' in resto:
        partes_ideas = resto.split('[YOUTUBE]', 1)
        analisis = partes_ideas[0].replace('[ANALISIS]', '').strip()
        ideas = '[YOUTUBE]' + partes_ideas[1]
    elif '[TIKTOK]' in resto:
        partes_ideas = resto.split('[TIKTOK]', 1)
        analisis = partes_ideas[0].replace('[ANALISIS]', '').strip()
        ideas = '[TIKTOK]' + partes_ideas[1]
    elif '[INSTAGRAM]' in resto:
        partes_ideas = resto.split('[INSTAGRAM]', 1)
        analisis = partes_ideas[0].replace('[ANALISIS]', '').strip()
        ideas = '[INSTAGRAM]' + partes_ideas[1]
        
    return tendencias, analisis, ideas


if __name__ == "__main__":
    analizar_y_generar_ideas()
