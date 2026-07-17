"""
Análisis de sentimiento en comentarios con Gemini.

Lee los comentarios crudos de la BD, los envía a Gemini para análisis,
y guarda los insights resultantes.
"""

import os
import sys
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion
from utils import get_logger

logger = get_logger('analisis_comentarios')
load_dotenv()


def _construir_prompt_comentarios(comentarios_por_post):
    """Construye el prompt para que Gemini analice los comentarios."""

    contexto = ""
    for titulo, comentarios in comentarios_por_post.items():
        contexto += f"\n[Post: \"{titulo}\"]\n"
        for com in comentarios[:30]:  # Máximo 30 por post para no exceder tokens
            contexto += f"  - \"{com['texto']}\" ({com['autor']})\n"

    return f"""
Analiza estos comentarios reales de las publicaciones de Instagram de @itsbgart,
una artista que hace papel reciclado artesanal e ilustraciones en acuarela.

COMENTARIOS DE LAS ÚLTIMAS 2 SEMANAS:
{contexto}

Responde EXACTAMENTE con este formato JSON (sin markdown, sin ```):

{{
  "sentimiento": "positivo",
  "pct_positivo": 85,
  "temas": ["proceso creativo", "encargos personalizados", "materiales artísticos", "inspiración viajes", "papel reciclado"],
  "preguntas": ["¿Cómo haces el papel reciclado?", "¿Haces envíos internacionales?", "¿Cuánto cuesta un encargo?", "¿Qué materiales usas?", "¿Cuánto tardas?"],
  "intenciones_compra": ["¿Tienes tienda?", "Me encantaría uno para regalar", "¿Haces encargos?", "¿Link en bio?"],
  "resumen": "Tu audiencia está muy interesada en el proceso de creación (especialmente el papel reciclado) y en los encargos personalizados. Hay demanda clara de contenido tutorial y de información sobre precios/disponibilidad. Las preguntas sobre envíos y tienda online indican oportunidad de conversión."
}}

REGLAS:
- "temas": los 5 temas que MÁS generan comentarios (ordenados por frecuencia)
- "preguntas": las preguntas reales que hace la audiencia (máximo 5, reformuladas de forma clara)
- "intenciones_compra": frases que indican interés en comprar/encargar (pueden ser 0 si no hay)
- "pct_positivo": porcentaje estimado de comentarios con sentimiento positivo
- "resumen": 2-3 frases accionables sobre qué quiere la audiencia
- Ignora spam, emojis solos, y comentarios de menos de 3 palabras
"""


def analizar_comentarios():
    """Ejecuta el análisis de sentimiento sobre los comentarios almacenados."""

    logger.info("🧠 Analizando sentimiento en comentarios...")

    # Inicializar Gemini
    clave_api = os.getenv('GEMINI_API_KEY')
    if not clave_api:
        try:
            from utils import obtener_config as _get_config
            clave_api = _get_config("GEMINI_API_KEY")
        except Exception:
            pass
    if not clave_api:
        try:
            import streamlit as st
            clave_api = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass

    if not clave_api:
        logger.warning("No se encontró GEMINI_API_KEY. Análisis de comentarios omitido.")
        return

    cliente_ia = genai.Client(api_key=clave_api)

    # Cargar comentarios recientes
    conexion = obtener_conexion()
    if not conexion:
        logger.error("No se pudo conectar a la BD")
        return

    try:
        cursor = conexion.cursor(dictionary=True)

        # Obtener comentarios de los últimos 14 días agrupados por post
        cursor.execute("""
            SELECT cr.texto, cr.autor, c.titulo
            FROM comentarios_raw cr
            JOIN contenidos c ON cr.id_contenido = c.id_contenido
            WHERE cr.plataforma = 'instagram'
              AND cr.fecha_extraccion >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
            ORDER BY c.fecha_publicacion DESC
        """)
        resultados = cursor.fetchall()

        if not resultados or len(resultados) < 5:
            logger.info("Pocos comentarios para analizar (mínimo 5). Esperando más datos.")
            cursor.close()
            conexion.close()
            return

        # Agrupar por post
        comentarios_por_post = {}
        for row in resultados:
            titulo = row['titulo'][:60]
            if titulo not in comentarios_por_post:
                comentarios_por_post[titulo] = []
            comentarios_por_post[titulo].append({
                'texto': row['texto'],
                'autor': row['autor'] or 'anon'
            })

        logger.info(f"📝 {len(resultados)} comentarios de {len(comentarios_por_post)} posts para analizar")

        # Generar análisis con Gemini
        prompt = _construir_prompt_comentarios(comentarios_por_post)

        respuesta = cliente_ia.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,  # Baja para respuestas más consistentes
                max_output_tokens=1500,
            ),
        )

        texto = respuesta.text.strip()
        if not texto:
            logger.warning("Gemini no generó respuesta para el análisis de comentarios.")
            cursor.close()
            conexion.close()
            return

        # Parsear JSON (Gemini a veces envuelve en ```)
        texto_limpio = texto.replace("```json", "").replace("```", "").strip()

        try:
            datos = json.loads(texto_limpio)
        except json.JSONDecodeError:
            logger.warning(f"No se pudo parsear la respuesta de Gemini como JSON: {texto_limpio[:200]}")
            # Guardar el resumen crudo si no es JSON válido
            cursor.execute("""
                INSERT INTO analisis_comentarios 
                (plataforma, resumen_ia)
                VALUES ('instagram', %s)
            """, (texto_limpio[:2000],))
            conexion.commit()
            cursor.close()
            conexion.close()
            return

        # Guardar en BD
        cursor.execute("""
            INSERT INTO analisis_comentarios 
            (plataforma, sentimiento_global, pct_positivo, temas_conversacion, 
             preguntas_frecuentes, intenciones_compra, resumen_ia)
            VALUES ('instagram', %s, %s, %s, %s, %s, %s)
        """, (
            datos.get('sentimiento', 'neutro'),
            datos.get('pct_positivo', 0),
            json.dumps(datos.get('temas', []), ensure_ascii=False),
            json.dumps(datos.get('preguntas', []), ensure_ascii=False),
            json.dumps(datos.get('intenciones_compra', []), ensure_ascii=False),
            datos.get('resumen', '')
        ))

        # Mantener solo los últimos 5 análisis
        cursor.execute("""
            DELETE FROM analisis_comentarios 
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id FROM analisis_comentarios ORDER BY fecha_analisis DESC LIMIT 5
                ) AS recientes
            )
        """)

        conexion.commit()
        logger.info(f"✅ Análisis de comentarios completado: {datos.get('sentimiento', '?')} ({datos.get('pct_positivo', 0)}% positivo)")

    except Exception as e:
        logger.error(f"Error en análisis de comentarios: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()


if __name__ == "__main__":
    analizar_comentarios()
