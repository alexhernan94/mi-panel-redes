import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Cargar las variables secretas del archivo .env
load_dotenv()

def obtener_conexion():
    """Establece y devuelve la conexión a la base de datos de Hostinger."""
    try:
        conexion = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            # Configuración recomendada para conexiones en la nube estables
            connect_timeout=10, 
            autocommit=True
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error crítico al conectar a MySQL de Hostinger: {e}")
        return None

# Código de prueba para ejecutar directamente en Codespaces
if __name__ == "__main__":
    print("Probando conexión con Hostinger...")
    con = obtener_conexion()
    if con:
        print("¡Conexión exitosa! Tu entorno de Codespaces ya se comunica con Hostinger.")
        con.close()
    else:
        print("La conexión ha fallado. Revisa tus credenciales o el acceso remoto de MySQL.")