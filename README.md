# 📊 Panel de Analítica | itsbgart

Cuadro de mandos privado para la marca **itsbgart** que centraliza las métricas de Instagram, TikTok y YouTube, y genera estrategia creativa con IA.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Cloud-red)
![License](https://img.shields.io/badge/License-Private-gray)

## Funcionalidades

- **Extracción automática** de métricas de Instagram (posts + stories + insights), TikTok y YouTube
- **Motor de IA** (Gemini) que analiza el rendimiento y genera ideas de contenido semanales
- **Planificador semanal** automático basado en datos reales de engagement por día
- **Detección de anomalías** (posts virales y bajo rendimiento) por plataforma
- **Mejor hora de publicación** segmentada por red social (hora Madrid)
- **Contenido evergreen** — identifica posts que siguen generando vistas semanas después
- **Benchmark vs sector** — compara tu engagement contra promedios del nicho arte/lifestyle
- **Calendario editorial** — visualiza tu cadencia de publicación
- **Renovación automática de tokens** (Instagram y TikTok)
- **Sincronización automática** 2x/día vía GitHub Actions

## Arquitectura

```
mi-panel-redes/
├── app.py                          # Panel Streamlit (UI principal)
├── conexion.py                     # Conexión a MySQL (Hostinger)
├── auth_tiktok.py                  # Autorización OAuth TikTok (PKCE)
├── extraccion/
│   ├── instagram.py                # Extractor IG (posts + stories + insights v22.0)
│   ├── tiktok.py                   # Extractor TT (auto-renovación token)
│   └── youtube.py                  # Extractor YT (detección Short/Largo)
├── procesamiento/
│   └── motor_ia.py                 # Motor Gemini (análisis + ideas + planificador)
├── .github/workflows/
│   ├── sincronizar_redes.yml       # Cron 2x/día (extracción de datos)
│   └── motor_ia_cron.yml           # Cron semanal (extracción + IA)
├── recargas_historico.py           # Script de recarga completa del histórico
├── tablas.sql                      # Estructura de la base de datos
├── requirements.txt                # Dependencias Python
└── GUIA_CREDENCIALES.md            # Guía para obtener todas las credenciales
```

## Requisitos

- Python 3.11+
- Base de datos MySQL (Hostinger)
- Cuentas de desarrollador en: Meta, TikTok, Google Cloud
- API Key de Gemini (Google AI Studio)

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
| `DB_HOST` | Hostinger → hPanel → Bases de datos → MySQL → Host | No caduca |
| `DB_USER` | Hostinger → hPanel → Bases de datos → Usuario creado | No caduca |
| `DB_PASSWORD` | Hostinger → hPanel → Bases de datos → Contraseña del usuario | No caduca |
| `DB_NAME` | Hostinger → hPanel → Bases de datos → Nombre de la BD | No caduca |
| `INSTAGRAM_TOKEN` | Meta → Graph API Explorer → Generate Access Token (con página seleccionada) → Extender a 60 días | Cada ~50 días (auto-renovable vía API) |
| `INSTAGRAM_ACCOUNT_ID` | Meta → Graph API Explorer → `me/accounts` → `{page_id}?fields=instagram_business_account` → copiar el `id` | No caduca |
| `META_CLIENT_ID` | Meta for Developers → Tu app → Configuración → Básica → ID de la aplicación | No caduca |
| `META_CLIENT_SECRET` | Meta for Developers → Tu app → Configuración → Básica → Clave secreta | No caduca |
| `TIKTOK_ACCESS_TOKEN` | Ejecutar `python auth_tiktok.py` → se guarda automáticamente | Cada 24h (auto-renovable con refresh token) |
| `TIKTOK_CLIENT_KEY` | TikTok for Developers → Tu app → Client Key | No caduca |
| `TIKTOK_CLIENT_SECRET` | TikTok for Developers → Tu app → Client Secret | No caduca |
| `TIKTOK_REFRESH_TOKEN` | Se genera con `python auth_tiktok.py` → se guarda automáticamente | Cada 365 días (re-ejecutar auth_tiktok.py) |
| `TIKTOK_REDIRECT_URI` | TikTok for Developers → Tu app → Platform: Web → Redirect URI | No caduca |
| `YOUTUBE_API_KEY` | Google Cloud Console → APIs y servicios → Credenciales → Clave de API | No caduca |
| `YOUTUBE_CHANNEL_ID` | YouTube Studio → Configuración → Canal → ID del canal (empieza por `UC...`) | No caduca |
| `GEMINI_API_KEY` | Google AI Studio (aistudio.google.com/apikey) → Create API Key | No caduca |
| `PANEL_PASSWORD` | La que tú elijas para proteger el acceso al panel | No caduca |

## Despliegue

### Streamlit Cloud

1. Conecta el repo en https://share.streamlit.io
2. Configura las variables en Settings → Secrets (formato TOML)
3. La app se despliega automáticamente en cada push

### GitHub Actions (automatización)

Configura los secrets en el repositorio (Settings → Secrets → Actions) para habilitar:
- **Sincronización 2x/día** (10:00 y 22:00 hora España)
- **Motor IA semanal** (lunes 09:00 hora España)

## Mantenimiento

| Tarea | Frecuencia | Qué hacer |
|---|---|---|
| Token Instagram | Cada ~50 días | Actualizar `INSTAGRAM_TOKEN` en secrets |
| Token TikTok | Cada 365 días | Ejecutar `python auth_tiktok.py` y actualizar secrets |
| YouTube / Gemini | Nunca | No caducan |

## Base de datos

```sql
-- Estructura principal (ver tablas.sql para el detalle completo)
contenidos          → Catálogo de publicaciones (id, plataforma, título, fecha, url)
metricas_rendimiento → Métricas por contenido y día (vistas, likes, compartidos, guardados)
insights_ia         → Historial de análisis generados por Gemini
```

## Stack tecnológico

- **Frontend:** Streamlit + Altair (visualización)
- **Backend:** Python + MySQL
- **IA:** Google Gemini 3.1 Flash Lite
- **APIs:** Meta Graph API v22.0, TikTok API v2, YouTube Data API v3
- **Hosting:** Streamlit Cloud (panel) + Hostinger (BD) + GitHub Actions (automatización)
