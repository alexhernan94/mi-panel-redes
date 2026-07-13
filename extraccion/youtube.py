import os
import sys
from datetime import datetime
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Esto permite que el script encuentre tu archivo conexion.py en la carpeta anterior
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion

load_dotenv()

# Configurar la conexión con YouTube
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def extraer_y_guardar_video(video_id):
    print(f"Buscando datos del vídeo: {video_id}...")
    
    # 1. Pedir los datos a YouTube
    respuesta = youtube.videos().list(
        part='snippet,statistics,contentDetails',
        id=video_id
    ).execute()

    if not respuesta['items']:
        print("No se encontró el vídeo.")
        return

    video = respuesta['items'][0]
    titulo = video['snippet']['title']
    fecha_pub_str = video['snippet']['publishedAt'] # Formato ISO
    
    # Convertir la fecha de YouTube para MySQL (de 2024-01-01T12:00:00Z a 2024-01-01 12:00:00)
    fecha_pub = datetime.strptime(fecha_pub_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
    
    vistas = int(video['statistics'].get('viewCount', 0))
    likes = int(video['statistics'].get('likeCount', 0))
    comentarios = int(video['statistics'].get('commentCount', 0))
    
    hoy = datetime.now().strftime("%Y-%m-%d")

    # 2. Guardar en la Base de Datos
    conexion = obtener_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            
            # Insertar en la tabla 'contenidos' (Usamos IGNORE para que no de error si el vídeo ya existe)
            sql_contenido = """
                INSERT IGNORE INTO contenidos 
                (id_contenido, plataforma, titulo, fecha_publicacion) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_contenido, (video_id, 'youtube', titulo, fecha_pub))

            # Insertar en la tabla 'metricas_rendimiento'
            sql_metricas = """
                INSERT INTO metricas_rendimiento 
                (id_contenido, fecha_registro, visualizaciones, likes, comentarios) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_metricas, (video_id, hoy, vistas, likes, comentarios))
            
            conexion.commit()
            print(f"¡Éxito! El vídeo '{titulo}' ({vistas} vistas) se ha guardado en Hostinger.")
            
        except Exception as e:
            print(f"Error al guardar en base de datos: {e}")
        finally:
            cursor.close()
            conexion.close()

# PRUEBA: Cambia este ID por el de uno de tus vídeos de YouTube
if __name__ == "__main__":
    ID_VIDEO_PRUEBA = "k1pnES5yqYk" # El código que va después de 'v=' en la URL
    extraer_y_guardar_video(ID_VIDEO_PRUEBA)