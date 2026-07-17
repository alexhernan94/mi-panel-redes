# Guía para resubmitir la app en TikTok for Developers

## Paso 1: Publicar las páginas web

Sube estos archivos a tu repo de GitHub Pages (`alexhernan94.github.io/itsbgart.github.io`):

| Archivo local | URL pública |
|---|---|
| `docs/landing/index.html` | `https://alexhernan94.github.io/itsbgart.github.io/index.html` |
| `docs/landing/callback.html` | `https://alexhernan94.github.io/itsbgart.github.io/callback.html` |
| `docs/privacy-policy.md` | Ya publicado: `https://alexhernan94.github.io/itsbgart.github.io/privacy.html` |
| `docs/terms-of-service.md` | Ya publicado: `https://alexhernan94.github.io/itsbgart.github.io/terms.html` |

Solo necesitas copiar `docs/landing/index.html` y `docs/landing/callback.html` a tu repo de GitHub Pages y hacer push.

## Paso 2: Configurar la app en TikTok Developers

Ve a https://developers.tiktok.com → tu app → editar:

### Información básica

| Campo | Valor |
|---|---|
| **App name** | CreatorMetrics |
| **App description** | CreatorMetrics is a social media analytics dashboard for content creators. Users can connect their TikTok account to view performance metrics (views, likes, shares, comments), track follower growth over time, analyze best posting times, and receive AI-powered content strategy recommendations. The platform supports multiple social networks (TikTok, Instagram, YouTube) in a unified interface. |
| **Category** | Business Services / Analytics |
| **App icon** | Un icono genérico de analytics (gráfico de barras) |

### URLs

| Campo | Valor |
|---|---|
| **Website URL** | `https://alexhernan94.github.io/itsbgart.github.io/` |
| **Privacy Policy URL** | `https://alexhernan94.github.io/itsbgart.github.io/privacy.html` |
| **Terms of Service URL** | `https://alexhernan94.github.io/itsbgart.github.io/terms.html` |
| **Redirect URI** | `https://alexhernan94.github.io/itsbgart.github.io/callback.html` |

### Plataforma

| Campo | Valor |
|---|---|
| **Platform** | Web |
| **Redirect URI** | `https://alexhernan94.github.io/itsbgart.github.io/callback.html` |

## Paso 3: Scopes a solicitar

Solicita solo estos dos scopes:
- `user.info.basic` — Para obtener nombre, avatar y conteo de seguidores
- `video.list` — Para obtener la lista de vídeos con sus métricas

## Paso 4: Capturas de pantalla

Sube 2-3 screenshots que muestren:

1. **Pantalla de conexión** — Tu pantalla de login del panel (la de "Introduce la clave de acceso")
2. **Dashboard con datos** — La pestaña General mostrando KPIs y gráficos
3. **Datos de TikTok** — La pestaña TikTok mostrando métricas (puedes usar datos de ejemplo)

### Tips para los screenshots:
- Que se vea "CreatorMetrics" como nombre (puedes cambiar el header temporalmente)
- Que se vean datos de múltiples plataformas (da sensación de producto real)
- No muestres el nombre "itsbgart" prominente — que parezca una herramienta genérica

## Paso 5: Use Case Description (campo de texto en la revisión)

Pega esto:

```
CreatorMetrics is a multi-platform social media analytics tool built for content creators.

How TikTok data is used:
1. Users authenticate their TikTok account via OAuth 2.0 (PKCE flow)
2. We fetch their video list and basic profile info (user.info.basic + video.list)
3. Metrics are displayed in a private dashboard alongside their Instagram and YouTube data
4. AI analyzes performance trends to suggest optimal posting strategies

User flow:
- User signs up → Connects TikTok account → Views unified analytics → Gets content recommendations

We do NOT:
- Display TikTok content publicly
- Access other users' data
- Share data with third parties
- Store raw video content

The app helps creators understand their audience and grow organically through data-driven decisions.
```

## Paso 6: Enviar a revisión

Haz clic en "Submit for review". La revisión suele tardar 1-5 días laborables.

## Después de la aprobación

Una vez aprobada:
1. Cambia el `TIKTOK_REDIRECT_URI` en la BD a `https://alexhernan94.github.io/itsbgart.github.io/callback.html`
2. Ejecuta `python auth_tiktok.py` para regenerar los tokens con la nueva redirect URI
3. Los tokens se guardarán automáticamente y la sincronización funcionará

## Si te rechazan de nuevo

Posibles motivos y soluciones:
- "Landing page not accessible" → Verifica que las URLs están online
- "Screenshots don't match description" → Asegúrate de que los screenshots muestran analytics multi-plataforma
- "Use case unclear" → Amplía la descripción del Use Case con más detalle del user flow
