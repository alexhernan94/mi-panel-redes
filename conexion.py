import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Cargar las variables secretas del archivo .env (local/Codespaces)
load_dotenv()

def _obtener_variable(nombre):
    """Lee una variable: primero de os.environ, luego de st.secrets como fallback."""
    valor = os.getenv(nombre)
    if valor:
        return valor
    # Fallback: leer de Streamlit secrets (cuando corre en Streamlit Cloud)
    try:
        import streamlit as st
        return st.secrets.get(nombre)
    except Exception:
        return None

def obtener_conexion():
    """Establece y devuelve la conexión a la base de datos de Hostinger."""
    try:
        conexion = mysql.connector.connect(
            host=_obtener_variable('DB_HOST'),
            user=_obtener_variable('DB_USER'),
            password=_obtener_variable('DB_PASSWORD'),
            database=_obtener_variable('DB_NAME'),
            connect_timeout=10, 
            autocommit=True
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error crítico al conectar a MySQL de Hostinger: {e}")
        return None

if __name__ == "__main__":
    print("Probando conexión con Hostinger...")
    con = obtener_conexion()
    if con:
        print("¡Conexión exitosa!")
        con.close()
    else:
        print("La conexión ha fallado. Revisa tus credenciales.")