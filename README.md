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
| Token Instagram expirado | El panel muestra 0 datos de IG o el log dice "Error API Meta: token expired" | 1. Ve al Graph API Explorer → genera token nuevo → 2. Actualiza en phpMyAdmin: `UPDATE configuracion SET valor='NUEVO_TOKEN' WHERE clave='INSTAGRAM_TOKEN'` |
| Refresh token TikTok expirado (>365 días sin sincronizar) | El log dice "No se pudo renovar TikTok" y la renovación falla | 1. Ejecuta `python auth_tiktok.py` → 2. Copia el nuevo token y refresh token → 3. Actualízalos en phpMyAdmin en la tabla `configuracion` |
| API Key YouTube no funciona | El log dice "API key not valid" | 1. Ve a Google Cloud Console → Credenciales → genera una nueva API Key → 2. Actualiza en phpMyAdmin: `UPDATE configuracion SET valor='AIza...' WHERE clave='YOUTUBE_API_KEY'` |
| Gemini no responde (429) | El log dice "RESOURCE_EXHAUSTED" | Espera unas horas — es un rate limit temporal del plan gratuito. Se resuelve solo. |
| La BD no conecta | El panel dice "Error al conectar con la base de datos" | 1. Verifica en Hostinger que MySQL remoto tiene `%` como IP → 2. Verifica que las credenciales de BD son correctas en Streamlit secrets |

### Dónde están las credenciales

| Tipo | Dónde se guardan | Cómo se modifican |
|---|---|---|
| Tokens dinámicos (IG, TikTok) | BD → tabla `configuracion` | Auto (scripts) o manual (phpMyAdmin) |
| Credenciales de BD | GitHub Actions secrets + Streamlit Cloud secrets | Manual en cada plataforma |
| API Keys fijas (YouTube, Gemini) | BD → tabla `configuracion` | Manual en phpMyAdmin |
| Contraseña del panel | Streamlit Cloud secrets | Manual en Streamlit settings |

### Cómo actualizar un token manualmente en phpMyAdmin

1. Entra en https://auth-db1501.hstgr.io (tu phpMyAdmin)
2. Selecciona la BD `u764199979_rrss_analytics`
3. Abre la tabla `configuracion`
4. Busca la fila con la `clave` que quieres cambiar
5. Haz doble clic en `valor` → pega el nuevo token → guarda

### Logs para diagnosticar problemas

Los scripts escriben logs en `logs/panel.log` (en ejecución local). Formato:
```
[2026-07-16 10:30:45] [instagram] INFO - ✅ Token renovado
[2026-07-16 10:30:46] [tiktok] WARNING - No se pudo renovar el token
[2026-07-16 10:31:02] [motor_ia] ERROR - 429 RESOURCE_EXHAUSTED
```

En GitHub Actions, los logs se ven en la pestaña Actions → selecciona la ejecución → haz clic en el step que falló.

## Base de datos

```sql
-- Estructura (ver tablas.sql para el detalle completo)
contenidos            → Catálogo de publicaciones (id, plataforma, título, fecha, url)
metricas_rendimiento  → Métricas por contenido y día (vistas, likes, compartidos, guardados)
insights_ia           → Historial de análisis generados por Gemini
seguidores_historico  → Evolución diaria de seguidores por plataforma
configuracion         → Tokens y credenciales que se auto-renuevan
```

## Stack tecnológico

- **Frontend:** Streamlit + Altair (visualización)
- **Backend:** Python + MySQL
- **IA:** Google Gemini 3.1 Flash Lite
- **APIs:** Meta Graph API v22.0, TikTok API v2, YouTube Data API v3
- **Hosting:** Streamlit Cloud (panel) + Hostinger (BD) + GitHub Actions (automatización)

