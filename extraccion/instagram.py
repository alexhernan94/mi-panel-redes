import os
import sys
import requests
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_logger, obtener_config, guardar_config
from conexion import obtener_conexion

logger = get_logger('instagram')

# Cargar .env como fallback (para ejecución local sin BD)
ruta_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(ruta_env)


def _cargar_credenciales():
    """Carga credenciales desde BD (prioridad) o .env (fallback)."""
    token = obtener_config("INSTAGRAM_TOKEN")
    account_id = obtener_config("INSTAGRAM_ACCOUNT_ID")
    return token, account_id


def auto_renovar_token_meta():
    """Renueva el token de Meta y lo guarda en la BD."""
    token_actual = obtener_config("INSTAGRAM_TOKEN")
    client_id = obtener_config("META_CLIENT_ID")
    client_secret = obtener_config("META_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logger.warning("No se puede auto-renovar: faltan META_CLIENT_ID o META_CLIENT_SECRET")
        return False
    if not token_actual:
        logger.warning("No hay token de Instagram para renovar")
        return False

    logger.info("🔄 Renovando token de Meta (Instagram)...")
    
    url = "https://graph.facebook.com/v22.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "fb_exchange_token": token_actual
    }

    try:
        respuesta = requests.get(url, params=params)
        datos = respuesta.json()

        if "access_token" in datos:
            nuevo_token = datos["access_token"]
            guardar_config("INSTAGRAM_TOKEN", nuevo_token)
            logger.info("✅ Token de Meta renovado correctamente (válido ~60 días más)")
            return True
        else:
            error_msg = datos.get("error", {}).get("message", "Error desconocido")
            logger.warning(f"No se pudo renovar el token: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"Error de conexión al renovar token: {e}")
        return False

def extraer_instagram():
    INSTAGRAM_TOKEN, INSTAGRAM_ACCOUNT_ID = _cargar_credenciales()
    
    if not INSTAGRAM_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        logger.warning("Extracción de Instagram omitida (faltan credenciales)")
        return
    
    # Intentar renovar el token antes de extraer
    auto_renovar_token_meta()
    # Recargar token por si se renovó
    INSTAGRAM_TOKEN = obtener_config("INSTAGRAM_TOKEN")
    
    logger.info("Conectando con Instagram (Métricas de Valor)...")
    
    # --- GUARDAR SEGUIDORES ---
    try:
        url_perfil = f"https://graph.facebook.com/v22.0/{INSTAGRAM_ACCOUNT_ID}?fields=followers_count&access_token={INSTAGRAM_TOKEN}"
        r_perfil = requests.get(url_perfil).json()
        if "followers_count" in r_perfil:
            _con = obtener_conexion()
            if _con:
                _cur = _con.cursor()
                _hoy = datetime.now().strftime('%Y-%m-%d')
                _cur.execute("""
                    INSERT INTO seguidores_historico (plataforma, seguidores, fecha_registro)
                    VALUES ('instagram', %s, %s)
                    ON DUPLICATE KEY UPDATE seguidores=%s
                """, (r_perfil['followers_count'], _hoy, r_perfil['followers_count']))
                _con.commit()
                _cur.close()
                _con.close()
                logger.info(f"👥 Seguidores Instagram: {r_perfil['followers_count']}")
    except Exception as e:
        print(f"   ⚠️ No se pudieron guardar seguidores: {e}")
    
    # --- PUBLICACIONES (Feed + Reels) ---
    url = f"https://graph.facebook.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media"
    
    params = {
        "fields": "id,media_type,caption,timestamp,like_count,comments_count,permalink,media_url",
        "access_token": INSTAGRAM_TOKEN,
        "limit": 10
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "error" in data:
        print(f"❌ Error API Meta: {data['error']['message']}")
        return
        
    publicaciones = data.get("data", [])
    
    # --- STORIES (últimas 24h activas) ---
    stories = []
    try:
        url_stories = f"https://graph.facebook.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/stories"
        params_stories = {
            "fields": "id,media_type,timestamp,permalink",
            "access_token": INSTAGRAM_TOKEN
        }
        response_stories = requests.get(url_stories, params=params_stories)
        data_stories = response_stories.json()
        
        if "data" in data_stories:
            stories = data_stories["data"]
            print(f"   📖 {len(stories)} stories activas detectadas")
    except Exception as e:
        print(f"   ⚠️ No se pudieron obtener stories: {e}")
    
    try:
        conexion = obtener_conexion()
        if not conexion:
            logger.error("No se pudo conectar a la BD")
            return
        cursor = conexion.cursor()
        
        # --- Guardar publicaciones del feed ---
        for pub in publicaciones:
            id_ig = pub["id"]
            tipo_raw = pub.get("media_type", "IMAGE")
            estilo_visual = "Carrusel" if tipo_raw == "CAROUSEL_ALBUM" else ("Reel" if tipo_raw == "VIDEO" else "Post Foto")
            titulo = pub.get("caption", "Sin título").split("\n")[0][:150]
            fecha_publicacion = pub["timestamp"].replace("T", " ").split("+")[0]
            
            likes = pub.get("like_count", 0)
            
            # --- SECCIÓN EXTRA DE MÉTRICAS DE VALOR (Insights específicos) ---
            url_insights = f"https://graph.facebook.com/v22.0/{id_ig}/insights"
            
            # v22.0: para Reels usar "views,saved,shares,reach", para fotos/carruseles "saved,shares,reach"
            if estilo_visual == "Reel":
                metricas_buscar = "views,saved,shares,reach"
            else:
                metricas_buscar = "saved,shares,reach"
            
            res_ins = requests.get(url_insights, params={"metric": metricas_buscar, "access_token": INSTAGRAM_TOKEN})
            data_ins = res_ins.json()
            
            guardados = 0
            compartidos_real = 0
            alcance = 0
            vistas = likes * 4  # Valor por defecto si no hay datos
            
            if "error" in data_ins:
                # Fallback: intentar solo con "saved"
                res_ins2 = requests.get(url_insights, params={"metric": "saved", "access_token": INSTAGRAM_TOKEN})
                data_ins = res_ins2.json()
            
            if "data" in data_ins:
                for metrica in data_ins["data"]:
                    if metrica["name"] == "saved":
                        guardados = metrica["values"][0]["value"]
                    elif metrica["name"] == "shares":
                        compartidos_real = metrica["values"][0]["value"]
                    elif metrica["name"] == "views":
                        vistas = metrica["values"][0]["value"]
                    elif metrica["name"] == "reach":
                        alcance = metrica["values"][0]["value"]
            
            # Comentarios (ya viene en la respuesta principal)
            comentarios = pub.get("comments_count", 0)
            
            # Si no hay compartidos reales de la API, estimar
            if compartidos_real == 0:
                compartidos_real = int((comentarios + guardados) * 0.8)

            # URL del post
            url_post = pub.get("permalink", "")

            # 1. Guardar contenido
            sql_contenido = """
                INSERT INTO contenidos (id_contenido, plataforma, titulo, estilo_visual, fecha_publicacion, url)
                VALUES (%s, 'instagram', %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE titulo=%s, estilo_visual=%s, url=%s
            """
            cursor.execute(sql_contenido, (id_ig, titulo, estilo_visual, fecha_publicacion, url_post, titulo, estilo_visual, url_post))
            
            # 2. Guardar métricas (con comentarios y alcance)
            fecha_registro = fecha_publicacion.split(" ")[0]
            sql_metrica = """
                INSERT INTO metricas_rendimiento (id_contenido, fecha_registro, visualizaciones, likes, compartidos, guardados, comentarios, alcance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE visualizaciones=%s, likes=%s, compartidos=%s, guardados=%s, comentarios=%s, alcance=%s
            """
            cursor.execute(sql_metrica, (id_ig, fecha_registro, vistas, likes, compartidos_real, guardados, comentarios, alcance, vistas, likes, compartidos_real, guardados, comentarios, alcance))
        
        # --- Guardar stories con insights completos ---
        for story in stories:
            id_story = story["id"]
            estilo_visual = "Story"
            fecha_publicacion = story["timestamp"].replace("T", " ").split("+")[0]
            fecha_registro = fecha_publicacion.split(" ")[0]
            url_story = story.get("permalink", "")
            
            # Obtener insights completos de la story
            impressions = 0
            reach = 0
            replies = 0
            taps_back = 0
            
            try:
                url_ins_story = f"https://graph.facebook.com/v22.0/{id_story}/insights"
                # Métricas de story válidas en API v22.0+
                # 'impressions' fue reemplazado por 'views' en v22.0
                metricas_story = "reach,replies,views"
                res_story = requests.get(url_ins_story, params={
                    "metric": metricas_story, 
                    "access_token": INSTAGRAM_TOKEN
                })
                data_story_ins = res_story.json()
                
                if "error" in data_story_ins:
                    error_msg = data_story_ins["error"].get("message", "Error desconocido")
                    print(f"   ⚠️ Story {id_story[:15]}: API error → {error_msg}")
                    # Intentar solo con 'views'
                    res_story2 = requests.get(url_ins_story, params={
                        "metric": "views", 
                        "access_token": INSTAGRAM_TOKEN
                    })
                    data_story_ins = res_story2.json()
                
                if "data" in data_story_ins:
                    for metrica in data_story_ins["data"]:
                        if metrica["name"] == "views":
                            impressions = metrica["values"][0]["value"]
                        elif metrica["name"] == "reach":
                            reach = metrica["values"][0]["value"]
                        elif metrica["name"] == "replies":
                            replies = metrica["values"][0]["value"]
                    
                    logger.info(f"📊 Story {id_story[:15]}... → {impressions} vistas, {reach} alcance, {replies} respuestas")
                else:
                    print(f"   ⚠️ Story {id_story[:15]}... → Sin datos de insights (respuesta: {str(data_story_ins)[:100]})")
                    
            except Exception as e:
                print(f"   ⚠️ Error de conexión al pedir insights de story: {e}")
            
            # Mapeo a nuestras columnas:
            # visualizaciones = impressions (veces que se vio)
            # likes = reach (cuentas únicas que la vieron) 
            # compartidos = replies (respuestas = señal de engagement)
            # guardados = 0 (stories no tienen guardados)
            
            sql_contenido = """
                INSERT INTO contenidos (id_contenido, plataforma, titulo, estilo_visual, fecha_publicacion, url)
                VALUES (%s, 'instagram', 'Story', %s, %s, %s)
                ON DUPLICATE KEY UPDATE estilo_visual=%s, url=%s
            """
            cursor.execute(sql_contenido, (id_story, estilo_visual, fecha_publicacion, url_story, estilo_visual, url_story))
            
            sql_metrica = """
                INSERT INTO metricas_rendimiento (id_contenido, fecha_registro, visualizaciones, likes, compartidos, guardados)
                VALUES (%s, %s, %s, %s, %s, 0)
                ON DUPLICATE KEY UPDATE visualizaciones=%s, likes=%s, compartidos=%s
            """
            cursor.execute(sql_metrica, (id_story, fecha_registro, impressions, reach, replies, impressions, reach, replies))
            
        conexion.commit()
        logger.info(f" Éxito: {len(publicaciones)} posts + {len(stories)} stories de Instagram analizados.")
        
    except Exception as err:
        logger.error(f"Error BD: {err}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

if __name__ == "__main__":
    extraer_instagram()