"""Módulo de autenticación del panel."""

import os
import streamlit as st


def verificar_contrasena():
    """Devuelve True si el usuario está autenticado."""
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if st.session_state["autenticado"]:
        return True

    # Leer contraseña desde st.secrets o .env
    try:
        clave_correcta = st.secrets["PANEL_PASSWORD"]
    except Exception:
        clave_correcta = os.getenv("PANEL_PASSWORD")

    # Si no hay contraseña configurada, modo desarrollo libre
    if not clave_correcta:
        return True

    st.markdown("<br><br>", unsafe_allow_html=True)
    col_logo, col_login, col_espacio = st.columns([1, 2, 1])
    with col_login:
        st.markdown("<h2 style='text-align: center; font-family: Lora;'>itsbgart</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.8rem; color: #A39B8F; letter-spacing:1px;'>CUADRO DE MANDOS PRIVADO</p>", unsafe_allow_html=True)
        clave_introducida = st.text_input("Introduce la clave de acceso", type="password", placeholder="••••••••")
        if st.button("Entrar al Panel", use_container_width=True):
            if clave_introducida == clave_correcta:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta. Acceso denegado.")
    return False
