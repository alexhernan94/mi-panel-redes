import os
import sys
import requests
import mysql.connector
from dotenv import load_dotenv, set_key
from datetime import datetime

# Forzar lectura del .env en la raíz
ruta_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(ruta_env)

INSTAGRAM_TOKEN = os.getenv("INSTAGRAM_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

if not INSTAGRAM_TOKEN or not INSTAGRAM_ACCOUNT_ID:
    print("⚠️ Faltan credenciales de Instagram en el .env (se omitirá la extracción)")
    INSTAGRAM_DISPONIBLE = False
else:
    INSTAGRAM_DISPONIBLE = True

def auto_renovar_token_meta():
    """Llama a la API de Meta para extender la vida del token otros 60 días y lo guarda en el .env."""
    global INSTAGRAM_TOKEN
    
    print("🔄 Renovando token de Meta (Instagram)...")
    
    client_id = os.getenv("META_CLIENT_ID")
    client_secret = os.getenv("META_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("⚠️ No se puede auto-renovar: faltan META_CLIENT_ID o META_CLIENT_SECRET en .env")
        return False

    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "fb_exchange_token": INSTAGRAM_TOKEN
    }

    try:
        respuesta = requests.get(url, params=params)
        datos = respuesta.json()

        if "access_token" in datos:
            nuevo_token = datos["access_token"]
            # Guardar el nuevo token en el .env para futuras ejecuciones
            set_key(ruta_env, "INSTAGRAM_TOKEN", nuevo_token)
            INSTAGRAM_TOKEN = nuevo_token
            print("✅ Token de Meta renovado correctamente (válido ~60 días más)")
            return True
        else:
            error_msg = datos.get("error", {}).get("message", "Error desconocido")
            print(f"⚠️ No se pudo renovar el token: {error_msg}")
            print("   El token actual sigue siendo válido hasta que expire.")
            return False
    except Exception as e:
        print(f"⚠️ Error de conexión al renovar token: {e}")
        return False

def extraer_instagram():
    if not INSTAGRAM_DISPONIBLE:
        print("⚠️ Extracción de Instagram omitida (faltan credenciales)")
        return
    
    # Intentar renovar el token antes de extraer (silencioso si falla)
    auto_renovar_token_meta()
    
    print("Conectando con Instagram (Métricas de Valor)...")
    
    # --- PUBLICACIONES (Feed + Reels) ---
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
    
    params = {
        "fields": "id,media_type,caption,timestamp,like_count,comments_count,permalink",
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
        url_stories = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/stories"
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
        conexion = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
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
            
            # v22.0: para Reels usar "views,saved,shares", para fotos/carruseles "saved,shares"
            if estilo_visual == "Reel":
                metricas_buscar = "views,saved,shares"
            else:
                metricas_buscar = "saved,shares"
            
            res_ins = requests.get(url_insights, params={"metric": metricas_buscar, "access_token": INSTAGRAM_TOKEN})
            data_ins = res_ins.json()
            
            guardados = 0
            compartidos_real = 0
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
            
            # Si no hay compartidos reales de la API, estimar
            if compartidos_real == 0:
                compartidos_real = int((pub.get("comments_count", 0) + guardados) * 0.8)

            # URL del post
            url_post = pub.get("permalink", "")

            # 1. Guardar contenido
            sql_contenido = """
                INSERT INTO contenidos (id_contenido, plataforma, titulo, estilo_visual, fecha_publicacion, url)
                VALUES (%s, 'instagram', %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE titulo=%s, estilo_visual=%s, url=%s
            """
            cursor.execute(sql_contenido, (id_ig, titulo, estilo_visual, fecha_publicacion, url_post, titulo, estilo_visual, url_post))
            
            # 2. Guardar métricas
            fecha_registro = fecha_publicacion.split(" ")[0]
            sql_metrica = """
                INSERT INTO metricas_rendimiento (id_contenido, fecha_registro, visualizaciones, likes, compartidos, guardados)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE visualizaciones=%s, likes=%s, compartidos=%s, guardados=%s
            """
            cursor.execute(sql_metrica, (id_ig, fecha_registro, vistas, likes, compartidos_real, guardados, vistas, likes, compartidos_real, guardados))
        
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
                    
                    print(f"   📊 Story {id_story[:15]}... → {impressions} vistas, {reach} alcance, {replies} respuestas")
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
        print(f"✅ Éxito: {len(publicaciones)} posts + {len(stories)} stories de Instagram analizados.")
        
    except mysql.connector.Error as err:
        print(f"Error BD: {err}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

if __name__ == "__main__":
    extraer_instagram()