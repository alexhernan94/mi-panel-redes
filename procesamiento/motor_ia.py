import os
import sys
from google import genai
from google.genai import types


from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion

load_dotenv()

clave_api = os.getenv('GEMINI_API_KEY')
if not clave_api:
    print("Error: No se ha encontrado la variable GEMINI_API_KEY")
    sys.exit()

cliente_ia = genai.Client(api_key=clave_api)

def analizar_y_generar_ideas():
    print("Leyendo rendimiento de la base de datos...")
    conexion = obtener_conexion()
    if not conexion: return

    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Extraer el histórico mixto
        query = """
            SELECT c.plataforma, c.titulo, c.estilo_visual,
                   MAX(m.visualizaciones) as vistas, MAX(m.likes) as likes
            FROM contenidos c
            JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
            GROUP BY c.id_contenido, c.plataforma, c.titulo, c.estilo_visual
            ORDER BY vistas DESC
            LIMIT 5
        """
        cursor.execute(query)
        mejores_obras = cursor.fetchall()
        
        if not mejores_obras:
            print("No hay suficientes datos para el análisis.")
            return

        datos_contexto = ""
        for ob in mejores_obras:
            datos_contexto += f"- [{ob['plataforma'].upper()}] '{ob['titulo']}' ({ob['estilo_visual']}) -> Vistas: {ob['vistas']}\n"

        prompt = f"""
        Actúa como un director creativo y estratega experto en crecimiento de canales de YouTube y TikTok, de contenido especializado en arte, estética y narrativa visual de la marca 'itsbgart'.
        Analiza las métricas de rendimiento de mis últimas obras (Presta especial atención a los Guardados y Compartidos, que indican valor artístico y conexión emocional):       
        
        {datos_contexto}
        
        Genera una estrategia de contenido adaptada minuciosamente a la naturaleza de cada plataforma. 
        
        REGLAS ESTRICTAS DE FORMATO: 
        1. NO uses negritas (asteriscos) alrededor de las etiquetas de formato. Escribe exactamente [VIDEO LARGO], [SHORT], [TIKTOK VERTICAL], [REEL], [STORY] o [CARRUSEL].
        2. Respeta escrupulosamente los saltos de línea. Cada viñeta (-) debe ir en una línea nueva.

        Estructura el output EXACTAMENTE así:
        
        [ANALISIS]
        (Párrafo de 3 líneas analizando qué elementos VISUALES, colores o técnicas están haciendo que la gente GUARDE más los contenidos).
        
        [YOUTUBE]
        
        [VIDEO LARGO] Título de la idea 1
        - 👁️ **Dirección de Arte:** (Describe el plano de cámara, iluminación o paleta cromática)
        - 🎣 **Gancho Narrativo:** (El concepto de los primeros 5 segundos)

        [VIDEO LARGO] Título de la idea 2
        - 👁️ **Dirección de Arte:** (Describe el plano de cámara, iluminación o paleta cromática)
        - 🎣 **Gancho Narrativo:** (El concepto de los primeros 5 segundos)
        
        [SHORT] Título de la idea 3
        - 👁️ **Dirección de Arte:** (Estética del plano detalle)
        - 🎣 **Gancho Narrativo:** (Estímulo visual inicial)

        [SHORT] Título de la idea 4
        - 👁️ **Dirección de Arte:** (Estética del plano detalle)
        - 🎣 **Gancho Narrativo:** (Estímulo visual inicial)
        
        [TIKTOK]
        
        [TIKTOK VERTICAL] Título de la idea 1
        - 👁️ **Estímulo Visual:** (Qué pasa en pantalla en el segundo 1 para retener)
        - 🎵 **Ritmo/Sonido:** (Sugerencia del tipo de audio o ASMR o música ambiente o transición)
        
        [TIKTOK VERTICAL] Título de la idea 2
        - 👁️ **Estímulo Visual:** (Qué pasa en pantalla en el segundo 1 para retener)
        - 🎵 **Ritmo/Sonido:** (Sugerencia del tipo de audio o ASMR o música ambiente o transición)

        [TIKTOK VERTICAL] Título de la idea 3
        - 👁️ **Estímulo Visual:** (Qué pasa en pantalla en el segundo 1 para retener)
        - 🎵 **Ritmo/Sonido:** (Sugerencia del tipo de audio o ASMR o música ambiente o transición)
        
        [INSTAGRAM]
        
        [STORY] Título de la idea 1
        - 👁️ **Interacción:** (Sticker dinámico sobre proceso de color)
        - 🎣 **Gancho Visual:** (Composición del lienzo)

        [STORY] Título de la idea 2
        - 👁️ **Interacción:** (Uso de encuestas, preguntas o stickers)
        - 🎣 **Gancho Visual:** (Luz de estudio)
        
        [REEL] Título de la idea 1
        - 👁️ **Estímulo Visual:** (Transición fluida de color)
        - 🎵 **Ritmo/Sonido:** (Audio estético en tendencia

        [REEL] Título de la idea 2
        - 👁️ **Estímulo Visual:** (Plano cenital de mezcla de pintura)
        - 🎵 **Ritmo/Sonido:** (Audio relajante)

        [CARRUSEL] Título de la idea 1
        - 👁️ **Flujo Visual:** (Portada macro de textura -> Desglose de pasos de la ilustración)
        - 💬 **Llamada a la acción:** (Incentivo estético para que guarden la publicación)

        [CARRUSEL] Título de la idea 2
        - 👁️ **Flujo Visual:** (Comparativa de luz natural vs luz artificial en la obra)
        - 💬 **Llamada a la acción:** (Incentivo estético para que guarden la publicación)
        """

        print("Consultando a Gemini (Modelo: gemini-3.1-flash-lite)...")
        
        respuesta = cliente_ia.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.9,
                top_p=0.95,
                max_output_tokens=4000,
            ),
        )
        
        texto_completo = respuesta.text
        # Segmentación limpia para la base de datos
        partes = texto_completo.split('[YOUTUBE]')
        analisis = partes[0].replace('[ANALISIS]', '').strip()
        ideas_plataformas = "[YOUTUBE]" + partes[1]

        sql_insert = "INSERT INTO insights_ia (analisis_rendimiento, ideas_contenido) VALUES (%s, %s)"
        cursor.execute(sql_insert, (analisis, ideas_plataformas))
        conexion.commit()
        print("¡Estrategia segmentada guardada con éxito en Hostinger!")

    except Exception as e:
        print(f"Error en el motor de IA: {e}")
    finally:
        cursor.close()
        conexion.close()

if __name__ == "__main__":
    analizar_y_generar_ideas()