import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Conectar con el archivo base de datos en la raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion

load_dotenv()

TIKTOK_TOKEN = os.getenv('TIKTOK_ACCESS_TOKEN')

def extraer_y_guardar_tiktok():
    if not TIKTOK_TOKEN:
        print("Error: Falta TIKTOK_ACCESS_TOKEN en el archivo .env")
        return

    print("Conectando con la API de TikTok...")

    # Endpoint oficial de TikTok API v2 para listar vídeos de la cuenta autorizada
    # En la API v2 de TikTok, los 'fields' deben ir obligatoriamente en la URL
    url = "https://open.tiktokapis.com/v2/video/list/?fields=id,title,create_time,share_url,view_count,like_count,comment_count,share_count"
    
    headers = {
        "Authorization": f"Bearer {TIKTOK_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # El cuerpo (payload) ahora solo lleva la cantidad máxima de vídeos
    payload = {
        "max_count": 20
    }

    try:
        respuesta = requests.post(url, headers=headers, json=payload)
        datos = respuesta.json()

        if 'error' in datos and datos['error']['code'] != "ok":
            print(f"Error devuelto por TikTok: {datos['error']['message']}")
            return

        videos = datos.get('data', {}).get('videos', [])
        if not videos:
            print("No se encontraron vídeos o el token no tiene permisos suficientes.")
            return

        conexion = obtener_conexion()
        if not conexion:
            return

        cursor = conexion.cursor()
        hoy = datetime.now().strftime("%Y-%m-%d")

        for video in videos:
            id_video = video.get('id')
            # Extraer el título o poner un valor por defecto si está vacío
            titulo = video.get('title', 'Sin título')[:250] 
            url_video = video.get('share_url')

            # TikTok devuelve la fecha en formato Unix (ej: 1672531199)
            timestamp = video.get('create_time')
            fecha_pub = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

            # Métricas
            vistas = video.get('view_count', 0)
            likes = video.get('like_count', 0)
            comentarios = video.get('comment_count', 0)
            compartidos = video.get('share_count', 0)

            # 1. Guardar en el catálogo fijo (contenidos)
            sql_contenido = """
                INSERT IGNORE INTO contenidos 
                (id_contenido, plataforma, titulo, fecha_publicacion, url_publicacion, estilo_visual) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_contenido, (id_video, 'tiktok', titulo, fecha_pub, url_video, 'Vídeo vertical'))

            # 2. Guardar en el histórico diario (metricas_rendimiento)
            sql_metricas = """
                INSERT INTO metricas_rendimiento 
                (id_contenido, fecha_registro, visualizaciones, likes, comentarios, compartidos) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_metricas, (id_video, hoy, vistas, likes, comentarios, compartidos))
            
            print(f"Guardado en Hostinger: {titulo} ({vistas} vistas)")

        conexion.commit()
        print("¡Éxito! Las métricas de TikTok han sido almacenadas correctamente.")

    except Exception as e:
        print(f"Error técnico al ejecutar el extractor de TikTok: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conexion' in locals(): conexion.close()

if __name__ == "__main__":
    extraer_y_guardar_tiktok()