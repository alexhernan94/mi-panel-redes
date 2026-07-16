"""Módulo de envío de alertas por email (Gmail SMTP)."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_logger, obtener_config

logger = get_logger('alertas')

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def enviar_alerta(asunto: str, cuerpo_html: str) -> bool:
    """
    Envía un email de alerta al destinatario configurado.
    
    Args:
        asunto: Asunto del email
        cuerpo_html: Contenido HTML del email
    
    Returns:
        True si se envió correctamente, False en caso contrario
    """
    remitente = obtener_config("GMAIL_REMITENTE")
    destinatario = obtener_config("GMAIL_DESTINATARIO")
    password = obtener_config("GMAIL_APP_PASSWORD")

    if not all([remitente, destinatario, password]):
        logger.warning("Alerta no enviada: faltan credenciales de Gmail en la BD")
        return False

    mensaje = MIMEMultipart("alternative")
    mensaje["From"] = f"Panel itsbgart <{remitente}>"
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto

    # Versión texto plano (fallback)
    texto_plano = cuerpo_html.replace("<br>", "\n").replace("</p>", "\n")
    import re
    texto_plano = re.sub(r'<[^>]+>', '', texto_plano)

    mensaje.attach(MIMEText(texto_plano, "plain"))
    mensaje.attach(MIMEText(cuerpo_html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(remitente, password)
            servidor.sendmail(remitente, destinatario, mensaje.as_string())
        
        logger.info(f"📧 Alerta enviada: {asunto}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Error de autenticación Gmail. Verifica la App Password en la BD.")
        return False
    except Exception as e:
        logger.error(f"❌ Error al enviar email: {e}")
        return False
