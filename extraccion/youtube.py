import os
import sys
import re
from datetime import datetime
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Esto permite que el script encuentre tu archivo conexion.py en la carpeta anterior
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion
from utils import get_logger, obtener_config

logger = get_logger('youtube')

load_dotenv()

# Configurar la conexión con YouTube (lee de BD → .env → st.secrets)
YOUTUBE_API_KEY = obtener_config('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL_ID = obtener_config('YOUTUBE_CHANNEL_ID')


def parsear_duracion_iso(duracion_iso):
    """Convierte duración ISO 8601 (PT1H3M20S) a segundos totales."""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duracion_iso)
    if not match:
        return 0
    horas = int(match.group(1) or 0)
    minutos = int(match.group(2) or 0)
    segundos = int(match.group(3) or 0)
    return horas * 3600 + minutos * 60 + segundos


def extraer_y_guardar_video(video_id, youtube_client=None):
    """Extrae y guarda un vídeo individual por su ID."""
    if not youtube_client:
        youtube_client = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    print(f"Buscando datos del vídeo: {video_id}...")
    
    respuesta = youtube_client.videos().list(
        part='snippet,statistics,contentDetails',
        id=video_id
    ).execute()

    if not respuesta['items']:
        print("No se encontró el vídeo.")
        return

    video = respuesta['items'][0]
    titulo = video['snippet']['title']
    fecha_pub_str = video['snippet']['publishedAt']
    
    fecha_pub = datetime.strptime(fecha_pub_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
    
    vistas = int(video['statistics'].get('viewCount', 0))
    likes = int(video['statistics'].get('likeCount', 0))
    comentarios = int(video['statistics'].get('commentCount', 0))
    
    # Detectar si es un Short por la duración (≤60s) y formato vertical
    duracion_iso = video['contentDetails'].get('duration', 'PT0S')  # Ej: PT15S, PT3M20S
    segundos = parsear_duracion_iso(duracion_iso)
    estilo_visual = "Short" if segundos <= 60 else "Vídeo largo"
    
    # Usamos la fecha real de publicación del vídeo
    fecha_registro = datetime.strptime(fecha_pub_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

    conexion = obtener_conexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            
            url_video = f"https://www.youtube.com/watch?v={video_id}"
            
            sql_contenido = """
                INSERT INTO contenidos 
                (id_contenido, plataforma, titulo, fecha_publicacion, url, estilo_visual, duracion_segundos) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE titulo=%s, url=%s, estilo_visual=%s, duracion_segundos=%s
            """
            cursor.execute(sql_contenido, (video_id, 'youtube', titulo, fecha_pub, url_video, estilo_visual, segundos, titulo, url_video, estilo_visual, segundos))

            sql_metricas = """
                INSERT INTO metricas_rendimiento 
                (id_contenido, fecha_registro, visualizaciones, likes, comentarios) 
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE visualizaciones=%s, likes=%s, comentarios=%s
            """
            cursor.execute(sql_metricas, (video_id, fecha_registro, vistas, likes, comentarios, vistas, likes, comentarios))
            
            conexion.commit()
            print(f"  ✅ '{titulo}' ({vistas} vistas)")
            
        except Exception as e:
            print(f"Error al guardar en base de datos: {e}")
        finally:
            cursor.close()
            conexion.close()


def extraer_youtube():
    """Extrae los últimos vídeos del canal de YouTube automáticamente.
    
    Usa playlistItems() sobre la playlist 'uploads' del canal (1 unidad de cuota)
    en lugar de search() (100 unidades de cuota por llamada).
    """
    if not YOUTUBE_API_KEY:
        print("❌ Error: Falta YOUTUBE_API_KEY en el .env")
        return
    if not YOUTUBE_CHANNEL_ID:
        print("❌ Error: Falta YOUTUBE_CHANNEL_ID en el .env")
        return

    print("Conectando con YouTube Data API...")
    youtube_client = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    # --- GUARDAR SUSCRIPTORES ---
    try:
        canal_resp = youtube_client.channels().list(id=YOUTUBE_CHANNEL_ID, part='statistics,contentDetails').execute()
        if canal_resp.get('items'):
            subs = int(canal_resp['items'][0]['statistics'].get('subscriberCount', 0))
            from datetime import datetime as _dt
            _con = obtener_conexion()
            if _con:
                _cur = _con.cursor()
                _hoy = _dt.now().strftime('%Y-%m-%d')
                _cur.execute("""
                    INSERT INTO seguidores_historico (plataforma, seguidores, fecha_registro)
                    VALUES ('youtube', %s, %s)
                    ON DUPLICATE KEY UPDATE seguidores=%s
                """, (subs, _hoy, subs))
                _con.commit()
                _cur.close()
                _con.close()
                print(f"   👥 Suscriptores YouTube: {subs}")
    except Exception as e:
        print(f"   ⚠️ No se pudieron guardar suscriptores: {e}")

    # Obtener playlist de uploads del canal (mucho más eficiente que search)
    try:
        canal_resp = youtube_client.channels().list(
            id=YOUTUBE_CHANNEL_ID,
            part='contentDetails'
        ).execute()
        
        if not canal_resp.get('items'):
            print("❌ No se encontró el canal. Verifica YOUTUBE_CHANNEL_ID")
            return
        
        uploads_playlist_id = canal_resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        print(f"❌ Error al obtener playlist de uploads: {e}")
        return

    # Listar últimos 10 vídeos desde la playlist de uploads (1 unidad de cuota vs 100)
    try:
        playlist_resp = youtube_client.playlistItems().list(
            playlistId=uploads_playlist_id,
            part='contentDetails',
            maxResults=10
        ).execute()
    except Exception as e:
        print(f"❌ Error al listar vídeos: {e}")
        return

    videos_encontrados = playlist_resp.get('items', [])
    if not videos_encontrados:
        print("No se encontraron vídeos en el canal.")
        return

    print(f"📺 Procesando {len(videos_encontrados)} vídeos del canal...")
    for item in videos_encontrados:
        video_id = item['contentDetails']['videoId']
        extraer_y_guardar_video(video_id, youtube_client)

    print(f"✅ Éxito: {len(videos_encontrados)} vídeos de YouTube sincronizados.")


if __name__ == "__main__":
    extraer_youtube()