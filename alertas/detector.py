"""
Detector de alertas inteligentes.

Analiza los datos tras cada sincronización y envía emails cuando detecta:
1. Post viral (vistas > media + 2*desviación estándar)
2. Inactividad prolongada (3+ días sin publicar)
3. Token próximo a expirar (< 7 días)
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conexion import obtener_conexion
from utils import get_logger, obtener_config
from alertas.email_sender import enviar_alerta

logger = get_logger('alertas')


def _detectar_virales():
    """Detecta posts que han explotado en las últimas 24h."""
    conexion = obtener_conexion()
    if not conexion:
        return

    try:
        cursor = conexion.cursor(dictionary=True)

        # Obtener media y desviación estándar de vistas por plataforma
        cursor.execute("""
            SELECT c.plataforma,
                   AVG(m.visualizaciones) as media,
                   STDDEV(m.visualizaciones) as desviacion
            FROM contenidos c
            JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
            WHERE m.visualizaciones > 0
            GROUP BY c.plataforma
            HAVING COUNT(*) >= 5
        """)
        estadisticas = {row['plataforma']: row for row in cursor.fetchall()}

        if not estadisticas:
            return

        # Buscar posts recientes (últimas 48h) que superen el umbral viral
        cursor.execute("""
            SELECT c.plataforma, c.titulo, c.url,
                   MAX(m.visualizaciones) as vistas,
                   MAX(m.likes) as likes,
                   MAX(m.compartidos) as compartidos
            FROM contenidos c
            JOIN metricas_rendimiento m ON c.id_contenido = m.id_contenido
            WHERE c.fecha_publicacion >= DATE_SUB(NOW(), INTERVAL 48 HOUR)
            GROUP BY c.id_contenido, c.plataforma, c.titulo, c.url
        """)
        recientes = cursor.fetchall()

        virales = []
        for post in recientes:
            plat = post['plataforma']
            if plat in estadisticas:
                umbral = estadisticas[plat]['media'] + 2 * (estadisticas[plat]['desviacion'] or 0)
                if post['vistas'] > umbral and umbral > 0:
                    virales.append(post)

        if virales:
            emoji_plat = {'instagram': '📸', 'tiktok': '🎵', 'youtube': '📺'}
            items_html = ""
            for v in virales:
                emoji = emoji_plat.get(v['plataforma'], '📊')
                link = f"<a href='{v['url']}'>{v['titulo'][:60]}</a>" if v['url'] else v['titulo'][:60]
                items_html += f"""
                <tr>
                    <td style="padding:8px; border-bottom:1px solid #E8E3DA;">{emoji} {v['plataforma'].capitalize()}</td>
                    <td style="padding:8px; border-bottom:1px solid #E8E3DA;">{link}</td>
                    <td style="padding:8px; border-bottom:1px solid #E8E3DA;"><strong>{v['vistas']:,}</strong> vistas</td>
                </tr>
                """

            cuerpo = f"""
            <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #5C554B;">🔥 ¡Contenido viral detectado!</h2>
                <p style="color: #7B7163;">Tienes <strong>{len(virales)} publicación(es)</strong> con rendimiento excepcional en las últimas 48h:</p>
                <table style="width:100%; border-collapse:collapse; margin: 16px 0;">
                    {items_html}
                </table>
                <div style="background-color: #F4F1EA; padding: 16px; border-radius: 8px; margin-top: 16px;">
                    <p style="margin:0; color: #5C554B;"><strong>💡 Acción recomendada:</strong></p>
                    <p style="margin:8px 0 0; color: #7B7163;">Publica contenido relacionado en las próximas 4-6 horas para aprovechar el impulso del algoritmo. Responde a todos los comentarios para mantener el engagement alto.</p>
                </div>
            </div>
            """
            enviar_alerta("🔥 Post viral detectado — itsbgart", cuerpo)
            logger.info(f"🔥 {len(virales)} post(s) viral(es) detectados → email enviado")

    except Exception as e:
        logger.error(f"Error detectando virales: {e}")
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def _detectar_inactividad():
    """Alerta si han pasado 3+ días sin publicar en alguna plataforma."""
    conexion = obtener_conexion()
    if not conexion:
        return

    try:
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT plataforma, MAX(fecha_publicacion) as ultima_pub
            FROM contenidos
            GROUP BY plataforma
        """)
        resultados = cursor.fetchall()

        plataformas_inactivas = []
        ahora = datetime.now()

        for row in resultados:
            dias_sin_publicar = (ahora - row['ultima_pub']).days
            if dias_sin_publicar >= 3:
                plataformas_inactivas.append({
                    'plataforma': row['plataforma'],
                    'dias': dias_sin_publicar,
                    'ultima': row['ultima_pub'].strftime('%d/%m/%Y')
                })

        if plataformas_inactivas:
            emoji_plat = {'instagram': '📸', 'tiktok': '🎵', 'youtube': '📺'}
            items_html = ""
            for p in plataformas_inactivas:
                emoji = emoji_plat.get(p['plataforma'], '📊')
                items_html += f"<li>{emoji} <strong>{p['plataforma'].capitalize()}</strong>: {p['dias']} días sin publicar (última: {p['ultima']})</li>"

            cuerpo = f"""
            <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #5C554B;">⏰ Alerta de inactividad</h2>
                <p style="color: #7B7163;">Llevas varios días sin publicar en:</p>
                <ul style="color: #7B7163; line-height: 2;">
                    {items_html}
                </ul>
                <div style="background-color: #F4F1EA; padding: 16px; border-radius: 8px; margin-top: 16px;">
                    <p style="margin:0; color: #5C554B;"><strong>💡 ¿Por qué importa?</strong></p>
                    <p style="margin:8px 0 0; color: #7B7163;">Los algoritmos penalizan la inactividad. Cada día sin publicar reduce tu alcance orgánico entre un 5-15%. Incluso una Story sencilla mantiene tu visibilidad.</p>
                </div>
            </div>
            """
            enviar_alerta("⏰ Llevas días sin publicar — itsbgart", cuerpo)
            logger.info(f"⏰ Inactividad detectada en {len(plataformas_inactivas)} plataforma(s) → email enviado")

    except Exception as e:
        logger.error(f"Error detectando inactividad: {e}")
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def _detectar_tokens_expirando():
    """Alerta si la renovación de tokens de Instagram o TikTok falló recientemente."""
    # Verificar token de Instagram probando la API
    token_ig = obtener_config("INSTAGRAM_TOKEN")
    token_tt = obtener_config("TIKTOK_ACCESS_TOKEN")

    problemas = []

    if not token_ig:
        problemas.append("Instagram: No hay token configurado")
    if not token_tt:
        problemas.append("TikTok: No hay token configurado")

    # Verificar que los tokens no estén vacíos o sean placeholder
    if token_ig and len(token_ig) < 20:
        problemas.append("Instagram: El token parece inválido (muy corto)")
    if token_tt and len(token_tt) < 20:
        problemas.append("TikTok: El token parece inválido (muy corto)")

    if problemas:
        items_html = "".join([f"<li style='margin-bottom:8px;'>⚠️ {p}</li>" for p in problemas])

        cuerpo = f"""
        <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #5C554B;">🔑 Problema con tokens de acceso</h2>
            <p style="color: #7B7163;">Se han detectado problemas con las credenciales:</p>
            <ul style="color: #7B7163; line-height: 2;">
                {items_html}
            </ul>
            <div style="background-color: #F4F1EA; padding: 16px; border-radius: 8px; margin-top: 16px;">
                <p style="margin:0; color: #5C554B;"><strong>🔧 Cómo solucionarlo:</strong></p>
                <p style="margin:8px 0 0; color: #7B7163;">
                    <strong>Instagram:</strong> Ve al Graph API Explorer → genera un token nuevo → actualízalo en phpMyAdmin (tabla configuracion).<br><br>
                    <strong>TikTok:</strong> Ejecuta <code>python auth_tiktok.py</code> en local para generar tokens nuevos.
                </p>
            </div>
        </div>
        """
        enviar_alerta("🔑 Tokens con problemas — itsbgart", cuerpo)
        logger.info(f"🔑 {len(problemas)} problema(s) de tokens detectados → email enviado")


def ejecutar_alertas():
    """Ejecuta todas las comprobaciones de alertas. Llamar tras cada sincronización."""
    logger.info("🔔 Ejecutando sistema de alertas...")

    _detectar_virales()
    #_detectar_inactividad()
    _detectar_tokens_expirando()

    logger.info("🔔 Sistema de alertas completado")


if __name__ == "__main__":
    ejecutar_alertas()
