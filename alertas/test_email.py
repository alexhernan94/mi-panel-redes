"""
Script de prueba para verificar que el envío de emails funciona.
Ejecutar una vez: python alertas/test_email.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alertas.email_sender import enviar_alerta


def test():
    print("📧 Enviando email de prueba...")
    
    cuerpo = """
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #5C554B;">✅ Sistema de alertas configurado</h2>
        <p style="color: #7B7163;">
            Si estás leyendo esto, las alertas por email funcionan correctamente.
        </p>
        <p style="color: #7B7163;">
            A partir de ahora recibirás notificaciones cuando:
        </p>
        <ul style="color: #7B7163; line-height: 2;">
            <li>🔥 Un post se vuelva viral</li>
            <li>🔑 Un token tenga problemas</li>
        </ul>
    </div>
    """

    exito = enviar_alerta("✅ Test — Sistema de alertas activo", cuerpo)
    
    if exito:
        print("✅ ¡Email enviado! Revisa tu bandeja de entrada.")
    else:
        print("❌ No se pudo enviar. Revisa las credenciales en la tabla configuracion.")


if __name__ == "__main__":
    test()
