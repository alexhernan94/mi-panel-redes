# 📊 Panel de Analítica | itsbgart

Cuadro de mandos privado para la marca **itsbgart** que centraliza las métricas de Instagram, TikTok y YouTube, y genera estrategia creativa con IA.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Cloud-red)
![License](https://img.shields.io/badge/License-Private-gray)

## Funcionalidades

- **Extracción automática** de métricas de Instagram (posts + stories + insights + reach), TikTok y YouTube
- **Motor de IA** (Gemini) que analiza el rendimiento y genera ideas de contenido 2x/semana
- **Captions listos para copiar** generados por IA, optimizados para engagement
- **Planificador semanal** automático basado en datos reales de engagement por día
- **Sistema de objetivos** con proyección de crecimiento ("a este ritmo llegas el X")
- **Alertas por email** cuando un post se viraliza o un token tiene problemas
- **Detección de anomalías** (posts virales y bajo rendimiento) por plataforma
- **Mejor hora de publicación** segmentada por red social (hora Madrid)
- **Contenido evergreen** — identifica posts que siguen generando vistas semanas después
- **Benchmark vs sector** — compara tu engagement contra promedios del nicho arte/lifestyle
- **Calendario editorial** — visualiza tu cadencia de publicación
- **Correlación contenido → crecimiento** — qué posts generan nuevos seguidores
- **Análisis de hashtags por rendimiento** — no los más usados, sino los que mejor funcionan
- **Renovación automática de tokens** (Instagram y TikTok)
- **Sincronización automática** 2x/día vía GitHub Actions

## Arquitectura

```
mi-panel-redes/
├── app.py                          # Panel Streamlit (UI principal)
├── conexion.py                     # Conexión a MySQL (Hostinger)
├── auth_tiktok.py                  # Autorización OAuth TikTok (PKCE)
├── extraccion/
│   ├── instagram.py                # Extractor IG (posts + stories + insights + reach)
│   ├── tiktok.py                   # Extractor TT (auto-renovación token + comentarios)
│   └── youtube.py                  # Extractor YT (playlistItems + duración + comentarios)
├── procesamiento/
│   └── motor_ia.py                 # Motor Gemini (análisis + ideas + captions + planificador)
├── panel/
│   ├── __init__.py                 # Exports del paquete
│   ├── auth.py                     # Sistema de autenticación
│   ├── datos.py                    # Carga de datos desde BD
│   ├── utils.py                    # Funciones auxiliares + estilos CSS
│   └── objetivos.py                # Sistema de objetivos y proyecciones
├── alertas/
│   ├── __init__.py                 # Exports del módulo
│   ├── email_sender.py             # Envío de emails via Gmail SMTP
│   ├── detector.py                 # Detección de virales + tokens rotos
│   └── test_email.py              # Script para probar el envío
├── utils/
│   ├── config.py                   # Configuración centralizada (BD → env → secrets)
│   └── logger.py                   # Sistema de logging estructurado
├── .github/workflows/
│   ├── sincronizar_redes.yml       # Cron 2x/día (extracción + alertas)
│   └── motor_ia_cron.yml           # Cron 2x/semana (extracción + IA)
├── recargas_historico.py           # Script de recarga completa del histórico
├── tablas.sql                      # Estructura completa de la base de datos
├── migracion_nuevas_metricas.sql   # Migración: comentarios, alcance, duración
├── migracion_objetivos.sql         # Migración: tabla de objetivos
├── requirements.txt                # Dependencias Python (versiones pinadas)
└── GUIA_CREDENCIALES.md            # Guía para obtener todas las credenciales
```

## Métricas capturadas

| Métrica | Instagram | TikTok | YouTube |
|---|:---:|:---:|:---:|
| Visualizaciones/Views | ✅ | ✅ | ✅ |
| Likes | ✅ | ✅ | ✅ |
| Compartidos/Shares | ✅ | ✅ | — |
| Guardados/Saves | ✅ | — | — |
| Comentarios | ✅ | ✅ | ✅ |
| Alcance (Reach) | ✅ | — | — |
| Duración del vídeo | — | — | ✅ |
| Seguidores (histórico diario) | ✅ | ✅ | ✅ |

## Requisitos

- Python 3.11+
- Base de datos MySQL (Hostinger)
- Cuentas de desarrollador en: Meta, TikTok, Google Cloud
- API Key de Gemini (Google AI Studio)
- App Password de Gmail (para alertas por email)

## Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/mi-panel-redes.git
cd mi-panel-redes

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear archivo .env con tus credenciales (ver GUIA_CREDENCIALES.md)
cp .env.example .env
nano .env

# 4. Ejecutar el panel
streamlit run app.py
```

## Variables de entorno

Consulta la [Guía completa de credenciales](GUIA_CREDENCIALES.md) para instrucciones paso a paso de cómo obtener cada valor.

| Variable | Fuente | Renovación |
|---|---|---|
| `DB_HOST` | Hostinger → hPanel → Bases de datos | No caduca |
| `DB_USER` | Hostinger → hPanel → Bases de datos | No caduca |
| `DB_PASSWORD` | Hostinger → hPanel → Bases de datos | No caduca |
| `DB_NAME` | Hostinger → hPanel → Bases de datos | No caduca |
| `INSTAGRAM_TOKEN` | Meta → Graph API Explorer → Extender a 60 días | Auto-renovable (~50 días) |
| `INSTAGRAM_ACCOUNT_ID` | Meta → Graph API Explorer → `me/accounts` | No caduca |
| `META_CLIENT_ID` | Meta for Developers → Tu app → Configuración | No caduca |
| `META_CLIENT_SECRET` | Meta for Developers → Tu app → Configuración | No caduca |
| `TIKTOK_ACCESS_TOKEN` | `python auth_tiktok.py` → se guarda automáticamente | Auto-renovable (24h) |
| `TIKTOK_CLIENT_KEY` | TikTok for Developers → Tu app | No caduca |
| `TIKTOK_CLIENT_SECRET` | TikTok for Developers → Tu app | No caduca |
| `TIKTOK_REFRESH_TOKEN` | `python auth_tiktok.py` → se guarda automáticamente | 365 días |
| `YOUTUBE_API_KEY` | Google Cloud Console → Credenciales | No caduca |
| `YOUTUBE_CHANNEL_ID` | YouTube Studio → Configuración → Canal | No caduca |
| `GEMINI_API_KEY` | Google AI Studio → Create API Key | No caduca |
| `GMAIL_APP_PASSWORD` | Google Account → App Passwords | No caduca (mientras 2FA activo) |
| `GMAIL_REMITENTE` | Email desde el que se envían alertas | No caduca |
| `GMAIL_DESTINATARIO` | Email que recibe alertas (`itsbgart@gmail.com`) | No caduca |
| `PANEL_PASSWORD` | La que tú elijas para proteger el acceso | No caduca |

## Despliegue

### Streamlit Cloud

1. Conecta el repo en https://share.streamlit.io
2. Configura las variables en Settings → Secrets (formato TOML)
3. La app se despliega automáticamente en cada push

### GitHub Actions (automatización)

Configura los secrets en el repositorio (Settings → Secrets → Actions) para habilitar:
- **Sincronización 2x/día** (10:00 y 22:00 hora España) + alertas por email
- **Motor IA 2x/semana** (lunes y jueves 09:00 hora España)

## Sistema de alertas

Se envían emails automáticos a `itsbgart@gmail.com` cuando:

| Alerta | Cuándo se dispara |
|---|---|
| 🔥 Post viral | Vistas > media + 2σ en las últimas 48h |
| 🔑 Token con problemas | Token vacío o inválido detectado |

Para probar las alertas manualmente:
```bash
python alertas/test_email.py
```

## Sistema de objetivos

El panel incluye un widget de objetivos que:
- Muestra el progreso hacia la meta con barra visual
- Proyecta cuándo se alcanzará la meta basándose en la tendencia real
- Permite añadir nuevos objetivos directamente desde el panel

## Mantenimiento y resolución de problemas

### Sistema de credenciales

Los tokens que caducan se almacenan en la tabla `configuracion` de la BD. Se auto-renuevan con cada sincronización sin intervención manual.

```
Flujo de renovación automática:
1. El script lee el token actual desde la BD (tabla configuracion)
2. Llama a la API para renovarlo
3. Guarda el nuevo token en la BD
4. Siguiente ejecución → lee el token renovado
→ Funciona igual desde GitHub Actions, Streamlit Cloud, o local
```

### ¿Cuándo necesito intervenir manualmente?

| Situación | Cómo lo detecto | Qué hacer |
|---|---|---|
| Token Instagram expirado | Email de alerta 🔑 o panel sin datos IG | Graph API Explorer → genera token nuevo → phpMyAdmin |
| Refresh token TikTok expirado (>365 días) | Email de alerta 🔑 | Ejecutar `python auth_tiktok.py` |
| API Key YouTube no funciona | Log dice "API key not valid" | Google Cloud Console → nueva API Key → phpMyAdmin |
| Gemini no responde (429) | Log dice "RESOURCE_EXHAUSTED" | Esperar unas horas (rate limit temporal) |
| La BD no conecta | Panel dice "Error al conectar" | Verificar Hostinger MySQL remoto tiene `%` como IP |

### Dónde están las credenciales

| Tipo | Dónde se guardan | Cómo se modifican |
|---|---|---|
| Tokens dinámicos (IG, TikTok) | BD → tabla `configuracion` | Auto (scripts) o manual (phpMyAdmin) |
| Credenciales de BD | GitHub Actions secrets + Streamlit Cloud secrets | Manual en cada plataforma |
| API Keys fijas (YouTube, Gemini) | BD → tabla `configuracion` | Manual en phpMyAdmin |
| Config email (Gmail) | BD → tabla `configuracion` + GitHub secret | Manual en phpMyAdmin |
| Contraseña del panel | Streamlit Cloud secrets | Manual en Streamlit settings |

### Logs para diagnosticar problemas

Los scripts escriben logs en `logs/panel.log` (en ejecución local). En GitHub Actions, los logs se ven en la pestaña Actions → selecciona la ejecución → haz clic en el step que falló.

## Base de datos

```sql
-- Estructura (ver tablas.sql para el detalle completo)
contenidos            → Catálogo de publicaciones (id, plataforma, título, formato, duración, fecha, url)
metricas_rendimiento  → Métricas por contenido (vistas, likes, compartidos, guardados, comentarios, alcance)
insights_ia           → Historial de análisis generados por Gemini
seguidores_historico  → Evolución diaria de seguidores por plataforma
configuracion         → Tokens y credenciales que se auto-renuevan
objetivos             → Metas de crecimiento con fecha límite
```

## Stack tecnológico

- **Frontend:** Streamlit + Altair (visualización)
- **Backend:** Python + MySQL
- **IA:** Google Gemini 3.1 Flash Lite
- **APIs:** Meta Graph API v22.0, TikTok API v2, YouTube Data API v3
- **Alertas:** Gmail SMTP
- **Hosting:** Streamlit Cloud (panel) + Hostinger (BD) + GitHub Actions (automatización)
