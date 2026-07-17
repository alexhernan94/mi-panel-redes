"""
Extractor de comentarios de Instagram.

Extrae el texto de los comentarios de los posts recientes para
alimentar el análisis de sentimiento con Gemini.
"""

import os
import sys
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion
from utils import get_logger, obtener_config

logger = get_logger('comentarios_ig')


def extraer_comentarios_instagram():
    """Extrae comentarios de los posts recientes de Instagram y los guarda en BD."""

    token = obtener_config("INSTAGRAM_TOKEN")
    if not token:
        logger.warning("Extracción de comentarios omitida (falta INSTAGRAM_TOKEN)")
        return

    logger.info("💬 Extrayendo comentarios de Instagram...")

    # Obtener posts recientes que tengan comentarios
    conexion = obtener_conexion()
    if not conexion:
        logger.error("No se pudo conectar a la BD")
        return

    try:
        cursor = conexion.cursor(dictionary=True)

        # Posts de IG de los últimos 14 días que aún no tienen comentarios extraídos
        cursor.execute("""
            SELECT c.id_contenido
            FROM contenidos c
            WHERE c.plataforma = 'instagram'
              AND c.estilo_visual != 'Story'
              AND c.fecha_publicacion >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
              AND c.id_contenido NOT IN (
                  SELECT DISTINCT id_contenido FROM comentarios_raw WHERE plataforma = 'instagram'
              )
            ORDER BY c.fecha_publicacion DESC
            LIMIT 10
        """)
        posts_pendientes = cursor.fetchall()

        if not posts_pendientes:
            logger.info("💬 Todos los posts recientes ya tienen comentarios extraídos.")
            cursor.close()
            conexion.close()
            return

        total_comentarios = 0

        for post in posts_pendientes:
            id_post = post['id_contenido']

            # Pedir comentarios de este post a la API de Meta
            url = f"https://graph.facebook.com/v22.0/{id_post}/comments"
            params = {
                "fields": "text,username,timestamp",
                "limit": 50,
                "access_token": token
            }

            try:
                response = requests.get(url, params=params)
                data = response.json()

                if "error" in data:
                    # Algunos posts no permiten leer comentarios (privacidad)
                    continue

                comentarios = data.get("data", [])
                if not comentarios:
                    continue

                for com in comentarios:
                    texto = com.get("text", "").strip()
                    if not texto or len(texto) < 2:
                        continue

                    autor = com.get("username", "")
                    fecha_str = com.get("timestamp", "")
                    fecha_com = None
                    if fecha_str:
                        fecha_com = fecha_str.replace("T", " ").split("+")[0]

                    cursor.execute("""
                        INSERT IGNORE INTO comentarios_raw 
                        (id_contenido, plataforma, texto, autor, fecha_comentario)
                        VALUES (%s, 'instagram', %s, %s, %s)
                    """, (id_post, texto[:1000], autor[:100], fecha_com))
                    total_comentarios += 1

            except Exception as e:
                logger.warning(f"Error extrayendo comentarios de {id_post[:15]}: {e}")
                continue

        conexion.commit()
        logger.info(f"💬 {total_comentarios} comentarios extraídos de {len(posts_pendientes)} posts")

    except Exception as e:
        logger.error(f"Error en extracción de comentarios: {e}")
    finally:
        if cursor:
            cursor.close()
        if conexion.is_connected():
            conexion.close()


if __name__ == "__main__":
    extraer_comentarios_instagram()
