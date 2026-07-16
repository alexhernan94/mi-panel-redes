"""
🔄 RECARGA COMPLETA DEL HISTÓRICO
===================================
Este script limpia las tablas de datos y re-extrae TODO el contenido
desde las APIs de Instagram, TikTok y YouTube con fechas correctas y normalizadas.

Ejecutar UNA VEZ para corregir el histórico:
    python recarga_historico_completo.py

Prerequisitos:
    - Tener todas las variables en .env correctamente configuradas
    - Tener el índice UNIQUE creado (fix_indice_metricas.sql)
"""

import os
import sys
import re
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from conexion import obtener_conexion

ruta_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(ruta_env)

# --- CONFIGURACIÓN ---
INSTAGRAM_TOKEN = os.getenv("INSTAGRAM_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
TIKTOK_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")


def limpiar_tablas():
    """Vacía las tablas para empezar de cero con datos limpios."""
    print("\n🗑️  PASO 0: Limpiando tablas existentes...")
    conexion = obtener_conexion()
    if not conexion:
        print("❌ No se pudo conectar a la BD")
        sys.exit(1)
    
    cursor = conexion.cursor()
    
    # Limpiar datos (el orden importa por la FK)
    cursor.execute("DELETE FROM metricas_rendimiento")
    cursor.execute("DELETE FROM contenidos")
    conexion.commit()
    
    print("   ✅ Tablas limpiadas correctamente")
    cursor.close()
    conexion.close()


# ============================================================
# INSTAGRAM - Extracción completa con paginación
# ============================================================
def recarga_instagram():
    """Extrae publicaciones de Instagram desde 2025 usando paginación."""
    if not INSTAGRAM_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        print("\n⚠️  Instagram omitido (faltan credenciales)")
        return 0

    print("\n📸 PASO 1: Extrayendo histórico de Instagram (2025-2026)...")
    
    # Timestamp Unix del 1 de enero 2025 00:00:00 UTC
    FECHA_DESDE = 1735689600  # 2025-01-01T00:00:00Z
    
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "fields": "id,media_type,caption,timestamp,like_count,comments_count,permalink",
        "access_token": INSTAGRAM_TOKEN,
        "since": FECHA_DESDE,
        "limit": 25
    }
    
    todas_publicaciones = []
    pagina = 1
    seguir_paginando = True
    
    while url and seguir_paginando:
        print(f"   📄 Página {pagina}...")
        response = requests.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            print(f"   ❌ Error API Meta: {data['error']['message']}")
            break
        
        publicaciones = data.get("data", [])
        
        for pub in publicaciones:
            # Filtro extra de seguridad: solo posts de 2025 en adelante
            ts = pub.get("timestamp", "")
            if ts and ts[:4] >= "2025":
                todas_publicaciones.append(pub)
            elif ts and ts[:4] < "2025":
                # Si encontramos posts anteriores a 2025, dejamos de paginar
                seguir_paginando = False
                break
        
        # Siguiente página
        paging = data.get("paging", {})
        url = paging.get("next")
        params = {}  # Los params ya van incluidos en la URL "next"
        pagina += 1
        time.sleep(0.5)  # Respetar rate limits
    
    if not todas_publicaciones:
        print("   ⚠️  No se encontraron publicaciones en el rango 2025-2026")
        return 0
    
    print(f"   📦 {len(todas_publicaciones)} publicaciones (2025-2026) encontradas. Guardando...")
    
    conexion = obtener_conexion()
    if not conexion:
        return 0
    
    cursor = conexion.cursor()
    guardados_ok = 0
    
    for pub in todas_publicaciones:
        try:
            id_ig = pub["id"]
            tipo_raw = pub.get("media_type", "IMAGE")
            estilo_visual = "Carrusel" if tipo_raw == "CAROUSEL_ALBUM" else ("Reel" if tipo_raw == "VIDEO" else "Post Foto")
            
            caption = pub.get("caption", "Sin título")
            titulo = caption.split("\n")[0][:150] if caption else "Sin título"
            
            # URL del post en Instagram
            url_post = pub.get("permalink", "")
            
            # Fecha normalizada: YYYY-MM-DD HH:MM:SS
            ts_raw = pub["timestamp"]  # Formato: 2024-06-12T14:30:00+0000
            fecha_publicacion = ts_raw.replace("T", " ").split("+")[0]
            fecha_registro = fecha_publicacion.split(" ")[0]  # Solo YYYY-MM-DD
            
            likes = pub.get("like_count", 0)
            comentarios = pub.get("comments_count", 0)            
            # Intentar obtener insights avanzados (puede fallar en posts antiguos)
            guardados = 0
            vistas = likes * 4  # Estimación por defecto
            
            try:
                url_insights = f"https://graph.facebook.com/v22.0/{id_ig}/insights"
                if estilo_visual == "Reel":
                    metricas_buscar = "views,saved,shares"
                else:
                    metricas_buscar = "saved,shares"
                res_ins = requests.get(url_insights, params={"metric": metricas_buscar, "access_token": INSTAGRAM_TOKEN})
                data_ins = res_ins.json()
                
                if "error" in data_ins:
                    # Fallback: solo saved
                    res_ins2 = requests.get(url_insights, params={"metric": "saved", "access_token": INSTAGRAM_TOKEN})
                    data_ins = res_ins2.json()
                
                if "data" in data_ins:
                    for metrica in data_ins["data"]:
                        if metrica["name"] == "saved":
                            guardados = metrica["values"][0]["value"]
                        elif metrica["name"] == "shares":
                            compartidos = metrica["values"][0]["value"]
                        elif metrica["name"] == "views":
                            vistas = metrica["values"][0]["value"]
            except Exception:
                pass  # Insights no disponibles para este post
            
            if compartidos == 0:
                compartidos = int((comentarios + guardados) * 0.8)
            
            # Guardar contenido
            sql_contenido = """
                INSERT INTO contenidos (id_contenido, plataforma, titulo, estilo_visual, fecha_publicacion, url)
                VALUES (%s, 'instagram', %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE titulo=%s, estilo_visual=%s, url=%s
            """
            cursor.execute(sql_contenido, (id_ig, titulo, estilo_visual, fecha_publicacion, url_post, titulo, estilo_visual, url_post))
            
            # Guardar métricas
            sql_metrica = """
                INSERT INTO metricas_rendimiento (id_contenido, fecha_registro, visualizaciones, likes, compartidos, guardados)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE visualizaciones=%s, likes=%s, compartidos=%s, guardados=%s
            """
            cursor.execute(sql_metrica, (id_ig, fecha_registro, vistas, likes, compartidos, guardados, vistas, likes, compartidos, guardados))
            guardados_ok += 1
            
        except Exception as e:
            print(f"   ⚠️  Error en post {pub.get('id', '?')}: {e}")
            continue
        
        time.sleep(0.3)  # Rate limit para insights
    
    conexion.commit()
    
    # --- STORIES (últimas 24h activas) ---
    stories_guardadas = 0
    try:
        url_stories = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/stories"
        params_stories = {
            "fields": "id,media_type,timestamp,permalink",
            "access_token": INSTAGRAM_TOKEN
        }
        response_stories = requests.get(url_stories, params=params_stories)
        data_stories = response_stories.json()
        
        if "data" in data_stories and data_stories["data"]:
            print(f"   📖 {len(data_stories['data'])} stories activas detectadas")
            
            # Reconectar si es necesario
            conexion2 = obtener_conexion()
            if conexion2:
                cursor2 = conexion2.cursor()
                for story in data_stories["data"]:
                    try:
                        id_story = story["id"]
                        fecha_pub = story["timestamp"].replace("T", " ").split("+")[0]
                        fecha_reg = fecha_pub.split(" ")[0]
                        url_story = story.get("permalink", "")
                        
                        cursor2.execute("""
                            INSERT INTO contenidos (id_contenido, plataforma, titulo, estilo_visual, fecha_publicacion, url)
                            VALUES (%s, 'instagram', 'Story', 'Story', %s, %s)
                            ON DUPLICATE KEY UPDATE estilo_visual='Story'
                        """, (id_story, fecha_pub, url_story))
                        
                        cursor2.execute("""
                            INSERT INTO metricas_rendimiento (id_contenido, fecha_registro, visualizaciones, likes, compartidos, guardados)
                            VALUES (%s, %s, 0, 0, 0, 0)
                            ON DUPLICATE KEY UPDATE visualizaciones=visualizaciones
                        """, (id_story, fecha_reg))
                        stories_guardadas += 1
                    except Exception:
                        pass
                
                conexion2.commit()
                cursor2.close()
                conexion2.close()
    except Exception as e:
        print(f"   ⚠️  No se pudieron obtener stories: {e}")
    
    cursor.close()
    conexion.close()
    
    total = guardados_ok + stories_guardadas
    print(f"   ✅ Instagram: {guardados_ok} posts + {stories_guardadas} stories guardadas correctamente")
    return total


# ============================================================
# TIKTOK - Extracción completa con paginación
# ============================================================
def recarga_tiktok():
    """Extrae vídeos de TikTok desde 2025 usando paginación con cursor."""
    if not TIKTOK_TOKEN:
        print("\n⚠️  TikTok omitido (falta TIKTOK_ACCESS_TOKEN)")
        return 0
    
    print("\n🎵 PASO 2: Extrayendo histórico de TikTok (2025-2026)...")
    
    url = "https://open.tiktokapis.com/v2/video/list/?fields=id,title,create_time,share_url,view_count,like_count,comment_count,share_count"
    headers = {
        "Authorization": f"Bearer {TIKTOK_TOKEN}",
        "Content-Type": "application/json"
    }
    
    todos_videos = []
    cursor_paginacion = None
    pagina = 1
    
    while True:
        print(f"   📄 Página {pagina}...")
        payload = {"max_count": 20}
        if cursor_paginacion:
            payload["cursor"] = cursor_paginacion
        
        respuesta = requests.post(url, headers=headers, json=payload)
        datos = respuesta.json()
        
        if 'error' in datos and datos['error'].get('code') != "ok":
            print(f"   ❌ Error TikTok: {datos['error'].get('message', datos)}")
            break
        
        videos = datos.get('data', {}).get('videos', [])
        todos_videos.extend(videos)
        
        # Paginación con cursor
        has_more = datos.get('data', {}).get('has_more', False)
        cursor_paginacion = datos.get('data', {}).get('cursor')
        
        if not has_more or not cursor_paginacion:
            break
        
        pagina += 1
        time.sleep(0.5)
    
    if not todos_videos:
        print("   ⚠️  No se encontraron vídeos")
        return 0
    
    print(f"   📦 {len(todos_videos)} vídeos encontrados. Guardando...")
    
    conexion = obtener_conexion()
    if not conexion:
        return 0
    
    cursor = conexion.cursor()
    guardados_ok = 0
    
    for video in todos_videos:
        try:
            id_video = video.get('id')
            titulo = video.get('title', 'Sin título')[:250]
            url_video = video.get('share_url', '')
            
            # Fecha normalizada desde timestamp Unix
            timestamp = video.get('create_time', 0)
            
            # Filtro: solo vídeos de 2025 en adelante (1735689600 = 2025-01-01)
            if timestamp < 1735689600:
                continue
            
            fecha_pub = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            fecha_registro = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
            
            vistas = video.get('view_count', 0)
            likes = video.get('like_count', 0)
            compartidos = video.get('share_count', 0)
            
            # Guardar contenido
            sql_contenido = """
                INSERT INTO contenidos (id_contenido, plataforma, titulo, fecha_publicacion, url, estilo_visual)
                VALUES (%s, 'tiktok', %s, %s, %s, 'Vídeo vertical')
                ON DUPLICATE KEY UPDATE titulo=%s, url=%s
            """
            cursor.execute(sql_contenido, (id_video, titulo, fecha_pub, url_video, titulo, url_video))
            
            # Guardar métricas
            sql_metricas = """
                INSERT INTO metricas_rendimiento (id_contenido, fecha_registro, visualizaciones, likes, compartidos)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE visualizaciones=%s, likes=%s, compartidos=%s
            """
            cursor.execute(sql_metricas, (id_video, fecha_registro, vistas, likes, compartidos, vistas, likes, compartidos))
            guardados_ok += 1
            
        except Exception as e:
            print(f"   ⚠️  Error en vídeo {video.get('id', '?')}: {e}")
            continue
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    print(f"   ✅ TikTok: {guardados_ok}/{len(todos_videos)} vídeos guardados correctamente")
    return guardados_ok


# ============================================================
# YOUTUBE - Extracción completa con paginación
# ============================================================
def recarga_youtube():
    """Extrae vídeos del canal de YouTube desde 2025 usando paginación."""
    if not YOUTUBE_API_KEY or not YOUTUBE_CHANNEL_ID:
        print("\n⚠️  YouTube omitido (faltan YOUTUBE_API_KEY o YOUTUBE_CHANNEL_ID)")
        return 0
    
    print("\n📺 PASO 3: Extrayendo histórico de YouTube (2025-2026)...")
    
    from googleapiclient.discovery import build
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # Primero obtenemos el ID de la playlist "uploads" del canal
    canal_resp = youtube.channels().list(
        id=YOUTUBE_CHANNEL_ID,
        part='contentDetails'
    ).execute()
    
    if not canal_resp.get('items'):
        print("   ❌ No se encontró el canal. Verifica YOUTUBE_CHANNEL_ID")
        return 0
    
    uploads_playlist_id = canal_resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    # Paginar por la playlist de uploads (más eficiente que search y no gasta cuota extra)
    todos_video_ids = []
    next_page_token = None
    pagina = 1
    
    while True:
        print(f"   📄 Página {pagina}...")
        playlist_resp = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part='contentDetails',
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        
        for item in playlist_resp.get('items', []):
            todos_video_ids.append(item['contentDetails']['videoId'])
        
        next_page_token = playlist_resp.get('nextPageToken')
        if not next_page_token:
            break
        pagina += 1
    
    if not todos_video_ids:
        print("   ⚠️  No se encontraron vídeos en el canal")
        return 0
    
    print(f"   📦 {len(todos_video_ids)} vídeos encontrados. Obteniendo estadísticas...")
    
    conexion = obtener_conexion()
    if not conexion:
        return 0
    
    cursor = conexion.cursor()
    guardados_ok = 0
    
    # Procesamos en lotes de 50 (máximo de la API de videos)
    for i in range(0, len(todos_video_ids), 50):
        lote = todos_video_ids[i:i+50]
        ids_str = ",".join(lote)
        
        videos_resp = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=ids_str
        ).execute()
        
        for video in videos_resp.get('items', []):
            try:
                video_id = video['id']
                titulo = video['snippet']['title'][:250]
                fecha_pub_str = video['snippet']['publishedAt']
                
                # Normalizar fecha (puede venir con Z o con +00:00)
                fecha_pub_str_clean = fecha_pub_str.replace("Z", "").split("+")[0].split(".")[0]
                fecha_pub_dt = datetime.strptime(fecha_pub_str_clean, "%Y-%m-%dT%H:%M:%S")
                
                # Filtro: solo vídeos de 2025 en adelante
                if fecha_pub_dt.year < 2025:
                    continue
                
                fecha_pub = fecha_pub_dt.strftime("%Y-%m-%d %H:%M:%S")
                fecha_registro = fecha_pub_dt.strftime("%Y-%m-%d")
                
                vistas = int(video['statistics'].get('viewCount', 0))
                likes = int(video['statistics'].get('likeCount', 0))
                
                # Determinar estilo visual por duración (≤60s = Short)
                duracion_iso = video.get('contentDetails', {}).get('duration', 'PT0S')
                match_dur = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duracion_iso)
                segundos_total = 0
                if match_dur:
                    segundos_total = int(match_dur.group(1) or 0) * 3600 + int(match_dur.group(2) or 0) * 60 + int(match_dur.group(3) or 0)
                estilo_visual = "Short" if segundos_total <= 60 else "Vídeo largo"
                
                # URL del vídeo
                url_video = f"https://www.youtube.com/watch?v={video_id}"
                
                # Guardar contenido
                sql_contenido = """
                    INSERT INTO contenidos (id_contenido, plataforma, titulo, fecha_publicacion, url, estilo_visual)
                    VALUES (%s, 'youtube', %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE titulo=%s, url=%s, estilo_visual=%s
                """
                cursor.execute(sql_contenido, (video_id, titulo, fecha_pub, url_video, estilo_visual, titulo, url_video, estilo_visual))
                
                # Guardar métricas
                sql_metricas = """
                    INSERT INTO metricas_rendimiento (id_contenido, fecha_registro, visualizaciones, likes)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE visualizaciones=%s, likes=%s
                """
                cursor.execute(sql_metricas, (video_id, fecha_registro, vistas, likes, vistas, likes))
                guardados_ok += 1
                
            except Exception as e:
                print(f"   ⚠️  Error en vídeo {video.get('id', '?')}: {e}")
                continue
        
        conexion.commit()
        print(f"   📊 Procesados {min(i+50, len(todos_video_ids))}/{len(todos_video_ids)}...")
    
    cursor.close()
    conexion.close()
    
    print(f"   ✅ YouTube: {guardados_ok}/{len(todos_video_ids)} vídeos guardados correctamente")
    return guardados_ok


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🔄 RECARGA COMPLETA DEL HISTÓRICO (2025-2026)")
    print("=" * 60)
    print("\nEsto va a:")
    print("  1. BORRAR todos los datos actuales de las tablas")
    print("  2. Re-extraer el histórico de 2025 y 2026 de Instagram, TikTok y YouTube")
    print("  3. Guardar todo con fechas reales y formato normalizado")
    print("\n⚠️  IMPORTANTE: Los datos actuales se perderán y serán reemplazados.")
    
    confirmacion = input("\n¿Continuar? (escribe 'SI' para confirmar): ")
    
    if confirmacion.strip().upper() != "SI":
        print("Operación cancelada.")
        sys.exit(0)
    
    inicio = time.time()
    
    # Paso 0: Limpiar
    limpiar_tablas()
    
    # Paso 1: Instagram
    total_ig = recarga_instagram()
    
    # Paso 2: TikTok
    total_tt = recarga_tiktok()
    
    # Paso 3: YouTube
    total_yt = recarga_youtube()
    
    # Resumen final
    duracion = time.time() - inicio
    print("\n" + "=" * 60)
    print("✅ RECARGA COMPLETA FINALIZADA")
    print("=" * 60)
    print(f"\n   📸 Instagram: {total_ig} publicaciones")
    print(f"   🎵 TikTok:    {total_tt} vídeos")
    print(f"   📺 YouTube:   {total_yt} vídeos")
    print(f"   ⏱️  Tiempo:    {duracion:.1f} segundos")
    print(f"\n   Total: {total_ig + total_tt + total_yt} contenidos en la base de datos")
    print("\n💡 Ya puedes abrir tu panel con 'streamlit run app.py' y ver el histórico completo.")
