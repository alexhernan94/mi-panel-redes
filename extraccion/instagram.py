import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Conectar con el archivo base de datos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion

load_dotenv()

ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
IG_ACCOUNT_ID = os.getenv('IG_ACCOUNT_ID')

def extraer_y_guardar_instagram():
    if not ACCESS_TOKEN or not IG_ACCOUNT_ID:
        print("Faltan las credenciales de Instagram en el archivo .env")
        return

    print("Conectando con la API de Meta para leer Instagram...")
    
    # URL para pedir los últimos posts (media) y sus métricas
    url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
    parametros = {
        'fields': 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
        'access_token': ACCESS_TOKEN,
        'limit': 5 # Trae las últimas 5 publicaciones
    }

    try:
        respuesta = requests.get(url, params=parametros)
        datos = respuesta.json()

        if 'error' in datos:
            print(f"Error de Meta: {datos['error']['message']}")
            return

        publicaciones = datos.get('data', [])
        if not publicaciones:
            print("No se encontraron publicaciones en esta cuenta.")
            return

        conexion = obtener_conexion()
        if not conexion:
            return
            
        cursor = conexion.cursor()
        hoy = datetime.now().strftime("%Y-%m-%d")

        for post in publicaciones:
            id_post = post.get('id')
            # Coger la primera línea del texto como título (si no hay, poner 'Sin título')
            texto_completo = post.get('caption', 'Sin título')
            titulo = texto_completo.split('\n')[0][:250] 
            
            tipo = post.get('media_type') # Puede ser IMAGE, VIDEO (Reel) o CAROUSEL_ALBUM
            url_post = post.get('permalink')
            
            # Formatear la fecha para MySQL
            fecha_str = post.get('timestamp')
            fecha_pub = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M:%S")

            likes = post.get('like_count', 0)
            comentarios = post.get('comments_count', 0)

            # 1. Guardar en el catálogo fijo (contenidos)
            sql_contenido = """
                INSERT IGNORE INTO contenidos 
                (id_contenido, plataforma, titulo, fecha_publicacion, url_publicacion, estilo_visual) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_contenido, (id_post, 'instagram', titulo, fecha_pub, url_post, tipo))

            # 2. Guardar en el histórico diario (metricas_rendimiento)
            sql_metricas = """
                INSERT INTO metricas_rendimiento 
                (id_contenido, fecha_registro, likes, comentarios) 
                VALUES (%s, %s, %s, %s)
            """
            # Nota: Views y alcance requieren endpoints más complejos en IG, empezamos por interacciones.
            cursor.execute(sql_metricas, (id_post, hoy, likes, comentarios))
            
            print(f"Guardado: {titulo} ({likes} likes)")

        conexion.commit()
        print("¡Éxito! Las métricas de Instagram se han guardado en Hostinger.")

    except Exception as e:
        print(f"Error al ejecutar el extractor de Instagram: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conexion' in locals(): conexion.close()

if __name__ == "__main__":
    extraer_y_guardar_instagram()
    