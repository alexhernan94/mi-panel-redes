import os
import urllib.parse
import requests
from dotenv import load_dotenv, set_key

ruta_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(ruta_env)

CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
REDIRECT_URI = os.getenv('TIKTOK_REDIRECT_URI')

def obtener_token():
    print("--- ASISTENTE DE AUTORIZACIÓN DE TIKTOK ---")
    
    # 1. Generar el enlace mágico
    url_auth = f"https://www.tiktok.com/v2/auth/authorize/?client_key={CLIENT_KEY}&response_type=code&scope=user.info.basic,video.list&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    
    print("\n1. Haz clic (o copia y pega) en el siguiente enlace para abrirlo en tu navegador:")
    print(f"\n{url_auth}\n")
    print("2. Inicia sesión en TikTok y dale a 'Autorizar'.")
    print("3. La página te redirigirá a una web que dirá 'No se puede conectar' o un error similar. ¡ES NORMAL!")
    print("4. Copia la URL completa de esa página de error de la barra de direcciones de tu navegador.")
    
    # 2. Pedir al usuario que pegue la URL con el código
    url_respuesta = input("\n-> Pega la URL completa aquí y pulsa Enter: ")
    
    try:
        # Extraer el código secreto de la URL
        codigo = urllib.parse.parse_qs(urllib.parse.urlparse(url_respuesta).query)['code'][0]
    except Exception:
        print("\nError: No se pudo encontrar el 'code' en la URL. Asegúrate de copiar la URL completa.")
        return

    print("\nIntercambiando el código por tu Access Token definitivo...")
    
    # 3. Pedir el Token definitivo a TikTok
    url_token = "https://open.tiktokapis.com/v2/oauth/token/"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    datos = {
        'client_key': CLIENT_KEY,
        'client_secret': CLIENT_SECRET,
        'code': codigo,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    
    respuesta = requests.post(url_token, headers=headers, data=datos)
    datos_json = respuesta.json()
    
    if 'access_token' in datos_json:
        access_token = datos_json['access_token']
        refresh_token = datos_json.get('refresh_token', '')
        
        # Guardar automáticamente en el .env
        set_key(ruta_env, "TIKTOK_ACCESS_TOKEN", access_token)
        if refresh_token:
            set_key(ruta_env, "TIKTOK_REFRESH_TOKEN", refresh_token)
        
        print("\n🎉 ¡ÉXITO! Tokens guardados automáticamente en tu .env:")
        print(f"   TIKTOK_ACCESS_TOKEN = {access_token[:20]}...")
        if refresh_token:
            print(f"   TIKTOK_REFRESH_TOKEN = {refresh_token[:20]}...")
            print("\n   El refresh token se usará para renovar automáticamente el acceso (válido 365 días).")
    else:
        print("\nHubo un error al pedir el token:")
        print(datos_json)

if __name__ == "__main__":
    obtener_token()