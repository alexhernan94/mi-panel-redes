import os
import sys
import requests
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime

# 1. Forzamos a Python a buscar el archivo .env en la carpeta raíz exacta del proyecto
ruta_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(ruta_env)

# 2. Cargamos las variables
INSTAGRAM_TOKEN = os.getenv("INSTAGRAM_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# 3. Cortafuegos de seguridad
if not INSTAGRAM_TOKEN or not INSTAGRAM_ACCOUNT_ID:
    print("❌ ERROR: No se pudieron leer las credenciales de Instagram.")
    print(f"Token: {'OK' if INSTAGRAM_TOKEN else 'FALTA'} | ID: {'OK' if INSTAGRAM_ACCOUNT_ID else 'FALTA'}")
    print("Verifica tu archivo .env y asegúrate de haberlo guardado.")
    sys.exit()

def extraer_instagram():
    print("Conectando con la API Graph de Meta (Instagram)...")
    
    # Endpoint para listar las publicaciones y sus métricas base
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"

def extraer_instagram():
    print("Conectando con la API Graph de Meta (Instagram)...")
    
    # Endpoint para listar las publicaciones y sus métricas base
    # Solicitamos: id, tipo de formato, descripción (título), fecha de publicación y métricas de impacto
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "fields": "id,media_type,caption,timestamp,like_count,comments_count",
        "access_token": INSTAGRAM_TOKEN,
        "limit": 10 # Extraemos los últimos 10 contenidos
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "error" in data:
        print(f"Error devuelto por Meta: {data['error']['message']}")
        return
        
    publicaciones = data.get("data", [])
    if not publicaciones:
        print("No se encontraron publicaciones recientes en tu perfil.")
        return

    # Conexión a la base de datos de Hostinger
    try:
        conexion = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conexion.cursor()
        
        for pub in publicaciones:
            id_ig = pub["id"]
            
            # Formatear el tipo visual según lo que pide tu panel UX
            tipo_raw = pub.get("media_type", "IMAGE")
            if tipo_raw == "VIDEO":
                estilo_visual = "Reel" # En cuentas profesionales actuales, los vídeos son Reels
            elif tipo_raw == "CAROUSEL":
                estilo_visual = "Carrusel"
            else:
                estilo_visual = "Post Foto"
                
            # Limpiar el título (caption)
            titulo = pub.get("caption", "Publicación sin texto").split("\n")[0][:150]
            
            # Formatear la fecha de Meta (ISO) a formato SQL (YYYY-MM-DD HH:MM:SS)
            fecha_raw = pub["timestamp"] # Ej: 2026-07-10T14:47:04+0000
            fecha_publicacion = fecha_raw.replace("T", " ").split("+")[0]
            
            # Métricas
            likes = pub.get("like_count", 0)
            vistas = likes * 4 # Nota de diseño: La API básica de Meta no da 'views' de fotos fijas/carruseles de forma directa por privacidad, estimamos un ratio orgánico x4 para el gráfico global.
            
            # 1. Guardar o actualizar la obra en la tabla principal
            sql_contenido = """
                INSERT INTO contenidos (id_contenido, plataforma, titulo, estilo_visual, fecha_publicacion)
                VALUES (%s, 'instagram', %s, %s, %s)
                ON DUPLICATE KEY UPDATE titulo=%s, estilo_visual=%s
            """
            cursor.execute(sql_contenido, (id_ig, titulo, estilo_visual, fecha_publicacion, titulo, estilo_visual))
            
            # 2. Registrar las métricas en el histórico
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            sql_metrica = """
                INSERT INTO metricas_rendimiento (id_contenido, fecha_registro, visualizaciones, likes)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE visualizaciones=%s, likes=%s
            """
            cursor.execute(sql_metrica, (id_ig, fecha_hoy, vistas, likes, vistas, likes))
            
        conexion.commit()
        print(f"¡Éxito! Se han procesado y guardado {len(publicaciones)} obras de Instagram.")
        
    except mysql.connector.Error as err:
        print(f"Error de Base de Datos: {err}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

if __name__ == "__main__":
    extraer_instagram()