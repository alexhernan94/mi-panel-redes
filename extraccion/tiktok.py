import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv, set_key

# Conectar con el archivo base de datos en la raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion
from utils import get_logger

logger = get_logger('tiktok')

ruta_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(ruta_env)

TIKTOK_TOKEN = os.getenv('TIKTOK_ACCESS_TOKEN')
TIKTOK_CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
TIKTOK_CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
TIKTOK_REFRESH_TOKEN = os.getenv('TIKTOK_REFRESH_TOKEN')


def auto_renovar_token_tiktok():
    """Usa el refresh_token para obtener un nuevo access_token sin intervención del usuario."""
    global TIKTOK_TOKEN, TIKTOK_REFRESH_TOKEN

    print("🔄 Renovando token de TikTok...")

    if not TIKTOK_CLIENT_KEY or not TIKTOK_CLIENT_SECRET or not TIKTOK_REFRESH_TOKEN:
        print("⚠️ No se puede auto-renovar TikTok: faltan TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET o TIKTOK_REFRESH_TOKEN en .env")
        return False

    url = "https://open.tiktokapis.com/v2/oauth/token/"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    datos = {
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": TIKTOK_REFRESH_TOKEN
    }

    try:
        respuesta = requests.post(url, headers=headers, data=datos)
        datos_json = respuesta.json()

        if "access_token" in datos_json:
            nuevo_access = datos_json["access_token"]
            nuevo_refresh = datos_json.get("refresh_token", TIKTOK_REFRESH_TOKEN)

            # Guardar ambos tokens en el .env
            set_key(ruta_env, "TIKTOK_ACCESS_TOKEN", nuevo_access)
            set_key(ruta_env, "TIKTOK_REFRESH_TOKEN", nuevo_refresh)

            TIKTOK_TOKEN = nuevo_access
            TIKTOK_REFRESH_TOKEN = nuevo_refresh

            print("✅ Token de TikTok renovado correctamente")
            return True
        else:
            error_msg = datos_json.get("error", datos_json.get("message", "Error desconocido"))
            print(f"⚠️ No se pudo renovar el token de TikTok: {error_msg}")
            print("   Si el refresh_token ha expirado (>365 días), necesitas re-autorizar manualmente con auth_tiktok.py")
            return False
    except Exception as e:
        print(f"⚠️ Error de conexión al renovar token de TikTok: {e}")
        return False

def extraer_y_guardar_tiktok():
    global TIKTOK_TOKEN

    # Intentar renovar el token antes de extraer
    auto_renovar_token_tiktok()

    if not TIKTOK_TOKEN:
        print("⚠️ Extracción de TikTok omitida (falta TIKTOK_ACCESS_TOKEN)")
        return

    print("Conectando con la API de TikTok...")

    # --- GUARDAR SEGUIDORES ---
    try:
        url_user = "https://open.tiktokapis.com/v2/user/info/?fields=follower_count"
        r_user = requests.get(url_user, headers={"Authorization": f"Bearer {TIKTOK_TOKEN}"}).json()
        follower_count = r_user.get('data', {}).get('user', {}).get('follower_count')
        if follower_count is not None:
            _con = obtener_conexion()
            if _con:
                _cur = _con.cursor()
                _hoy = datetime.now().strftime('%Y-%m-%d')
                _cur.execute("""
                    INSERT INTO seguidores_historico (plataforma, seguidores, fecha_registro)
                    VALUES ('tiktok', %s, %s)
                    ON DUPLICATE KEY UPDATE seguidores=%s
                """, (follower_count, _hoy, follower_count))
                _con.commit()
                _cur.close()
                _con.close()
                print(f"   👥 Seguidores TikTok: {follower_count}")
    except Exception as e:
        print(f"   ⚠️ No se pudieron guardar seguidores TikTok: {e}")

    # Endpoint oficial de TikTok API v2 para listar vídeos de la cuenta autorizada
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
            compartidos = video.get('share_count', 0)

            # 1. Guardar en el catálogo fijo (contenidos)
            sql_contenido = """
                INSERT IGNORE INTO contenidos 
                (id_contenido, plataforma, titulo, fecha_publicacion, url, estilo_visual) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_contenido, (id_video, 'tiktok', titulo, fecha_pub, url_video, 'Vídeo vertical'))

            # 2. Guardar en el histórico diario (metricas_rendimiento)
            # Usamos la fecha real de publicación del vídeo, no la fecha de sincronización
            fecha_registro = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
            sql_metricas = """
                INSERT INTO metricas_rendimiento 
                (id_contenido, fecha_registro, visualizaciones, likes, compartidos) 
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE visualizaciones=%s, likes=%s, compartidos=%s
            """
            cursor.execute(sql_metricas, (id_video, fecha_registro, vistas, likes, compartidos, vistas, likes, compartidos))
            
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