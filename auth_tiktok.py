import os
import urllib.parse
import hashlib
import base64
import secrets
import requests
from dotenv import load_dotenv, set_key

ruta_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(ruta_env)

CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
REDIRECT_URI = os.getenv('TIKTOK_REDIRECT_URI')


def generar_code_challenge():
    """Genera code_verifier y code_challenge para PKCE (formato TikTok)."""
    # TikTok requiere un code_verifier de 43-128 caracteres alfanuméricos
    code_verifier = secrets.token_urlsafe(32)  # ~43 caracteres, URL-safe sin padding
    # code_challenge = base64url(sha256(code_verifier)) sin padding '='
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')
    return code_verifier, code_challenge


def obtener_token():
    print("--- ASISTENTE DE AUTORIZACIÓN DE TIKTOK (con PKCE) ---")
    
    if not CLIENT_KEY or not CLIENT_SECRET:
        print("\n❌ Error: Faltan TIKTOK_CLIENT_KEY o TIKTOK_CLIENT_SECRET en tu .env")
        return
    
    redirect_uri = REDIRECT_URI or "https://localhost:3000/"
    
    # Generar PKCE
    code_verifier, code_challenge = generar_code_challenge()
    
    # 1. Generar el enlace de autorización con code_challenge
    params = {
        'client_key': CLIENT_KEY,
        'response_type': 'code',
        'scope': 'user.info.basic,video.list',
        'redirect_uri': redirect_uri,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    url_auth = f"https://www.tiktok.com/v2/auth/authorize/?{urllib.parse.urlencode(params)}"
    
    print("\n1. Abre este enlace en tu navegador:")
    print(f"\n{url_auth}\n")
    print("2. Inicia sesión en TikTok y dale a 'Autorizar'.")
    print("3. Te redirigirá a una página que no carga (localhost). ¡ES NORMAL!")
    print("4. Copia la URL COMPLETA de la barra de direcciones del navegador.")
    
    # 2. Pedir al usuario que pegue la URL con el código
    url_respuesta = input("\n-> Pega la URL completa aquí y pulsa Enter: ")
    
    try:
        codigo = urllib.parse.parse_qs(urllib.parse.urlparse(url_respuesta).query)['code'][0]
    except Exception:
        print("\nError: No se pudo encontrar el 'code' en la URL. Asegúrate de copiar la URL completa.")
        return

    print("\nIntercambiando el código por tu Access Token...")
    
    # 3. Pedir el Token con code_verifier (PKCE)
    url_token = "https://open.tiktokapis.com/v2/oauth/token/"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    datos = {
        'client_key': CLIENT_KEY,
        'client_secret': CLIENT_SECRET,
        'code': codigo,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier,
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
            print("\n   El refresh token se usará para renovar automáticamente (válido 365 días).")
    else:
        print("\n❌ Error al obtener el token:")
        print(datos_json)


if __name__ == "__main__":
    obtener_token()
