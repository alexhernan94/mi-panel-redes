# Guía para recopilar todas las credenciales

## Formato final del archivo `.env`

```
DB_HOST=tu_valor
DB_USER=tu_valor
DB_PASSWORD=tu_valor
DB_NAME=tu_valor
INSTAGRAM_TOKEN=tu_valor
INSTAGRAM_ACCOUNT_ID=tu_valor
META_CLIENT_ID=tu_valor
META_CLIENT_SECRET=tu_valor
TIKTOK_ACCESS_TOKEN=tu_valor
TIKTOK_CLIENT_KEY=tu_valor
TIKTOK_CLIENT_SECRET=tu_valor
TIKTOK_REFRESH_TOKEN=tu_valor
TIKTOK_REDIRECT_URI=tu_valor
YOUTUBE_API_KEY=tu_valor
YOUTUBE_CHANNEL_ID=tu_valor
GEMINI_API_KEY=tu_valor
PANEL_PASSWORD=tu_valor
```

---

## 1. Base de datos (Hostinger)

### Dónde ir:

1. Entra en https://hpanel.hostinger.com
2. Menú lateral → **Bases de datos** → **MySQL**
3. Busca tu base de datos `u764199979_rrss_analytics`

### Qué copiar:

| Variable | Dónde encontrarla |
|---|---|
| `DB_HOST` | Aparece como "Host" debajo del nombre de la BD (ej: `auth-db1501.hstgr.io`) |
| `DB_USER` | El nombre de usuario que creaste (ej: `u764199979_admin`) |
| `DB_PASSWORD` | La contraseña que pusiste al crear el usuario. Si no la recuerdas, puedes cambiarla desde ahí |
| `DB_NAME` | El nombre de la base de datos (ej: `u764199979_rrss_analytics`) |

### Renovación:

No caducan. Solo cambian si tú los modificas manualmente en Hostinger.

---

## 2. Instagram / Meta

### Dónde ir:

1. Entra en https://developers.facebook.com
2. Arriba a la derecha → **Mis apps** → selecciona tu app
3. Menú lateral → **Configuración** → **Básica**

### Qué copiar:

| Variable | Dónde encontrarla |
|---|---|
| `META_CLIENT_ID` | El campo **"Identificador de la app"** (un número largo) |
| `META_CLIENT_SECRET` | El campo **"Clave secreta de la app"** (haz clic en "Mostrar") |

### Obtener el token de Instagram (`INSTAGRAM_TOKEN`):

1. Ve a https://developers.facebook.com/tools/explorer/
2. Selecciona tu app arriba a la derecha
3. En permisos, añade: `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`
4. Haz clic en **"Generate Access Token"**
5. **IMPORTANTE:** Cuando Facebook te pregunte "¿Qué páginas quieres usar?" → selecciona tu página de itsbgart
6. Si no te pregunta por páginas, revoca la app primero: Facebook → Configuración → Apps y sitios web → tu app → Eliminar. Luego repite desde el paso 1.
7. Copia el token generado

### Convertir a token de larga duración (60 días):

Abre en tu navegador (reemplaza los valores):

```
https://graph.facebook.com/v22.0/oauth/access_token?grant_type=fb_exchange_token&client_id=TU_META_CLIENT_ID&client_secret=TU_META_CLIENT_SECRET&fb_exchange_token=TU_TOKEN_CORTO
```

La respuesta JSON te da el `access_token` de larga duración. Usa ese como `INSTAGRAM_TOKEN`.

### Obtener el Account ID de Instagram (`INSTAGRAM_ACCOUNT_ID`):

**Opción A — Desde el Graph API Explorer:**

1. Con tu token ya generado (que incluya la página), ejecuta esta consulta:
   ```
   me/accounts?fields=id,name,instagram_business_account
   ```
2. Busca tu página en la respuesta → copia el `id` que aparece dentro de `instagram_business_account`
3. Ese número (empieza por `1784...`) es tu `INSTAGRAM_ACCOUNT_ID`

**Opción B — Desde Meta Business Manager:**

1. Ve a https://business.facebook.com/settings/
2. En el menú lateral: **Cuentas** → **Cuentas de Instagram**
3. Selecciona tu cuenta
4. En la URL del navegador verás: `.../instagram-account/17841400000000000/?business_id=...`
5. El número después de `/instagram-account/` es tu `INSTAGRAM_ACCOUNT_ID`

### Renovación:

| Variable | Caduca | Cómo renovar |
|---|---|---|
| `META_CLIENT_ID` | No | — |
| `META_CLIENT_SECRET` | No | — |
| `INSTAGRAM_TOKEN` | Cada ~60 días | El script lo auto-renueva vía API. Si falla, repetir el proceso manual |
| `INSTAGRAM_ACCOUNT_ID` | No | — |

---

## 3. TikTok

### Dónde ir:

1. Entra en https://developers.tiktok.com
2. **Manage apps** → selecciona tu app

### Qué copiar:

| Variable | Dónde encontrarla |
|---|---|
| `TIKTOK_CLIENT_KEY` | En la página de tu app, campo **"Client Key"** |
| `TIKTOK_CLIENT_SECRET` | Campo **"Client Secret"** |
| `TIKTOK_REDIRECT_URI` | En tu app → **Platform: Web** → campo "Redirect URI" (ej: `https://localhost:3000/`) |

### Obtener Access Token y Refresh Token:

1. En tu terminal local, ejecuta:
   ```bash
   python auth_tiktok.py
   ```
2. Te dará un enlace → ábrelo en el navegador → autoriza con tu cuenta de TikTok
3. Te redirigirá a una página que no carga (localhost). Esto es normal.
4. Copia la URL completa de la barra de direcciones del navegador
5. Pégala en la terminal
6. El script guardará automáticamente en tu `.env`:
   - `TIKTOK_ACCESS_TOKEN`
   - `TIKTOK_REFRESH_TOKEN`

### Notas:

- Si la app está en Sandbox, necesitas tu usuario de TikTok añadido como "Sandbox user" en la configuración de la app.
- La `TIKTOK_REDIRECT_URI` debe coincidir **exactamente** (con o sin `/` final, con o sin `https`) con la registrada en TikTok Developers.

### Renovación:

| Variable | Caduca | Cómo renovar |
|---|---|---|
| `TIKTOK_CLIENT_KEY` | No | — |
| `TIKTOK_CLIENT_SECRET` | No | — |
| `TIKTOK_REDIRECT_URI` | No | — |
| `TIKTOK_ACCESS_TOKEN` | Cada ~24h | Se auto-renueva con el refresh token |
| `TIKTOK_REFRESH_TOKEN` | Cada 365 días | Re-ejecutar `python auth_tiktok.py` |

---

## 4. YouTube

### Dónde ir:

1. Entra en https://console.cloud.google.com
2. Selecciona tu proyecto (o crea uno nuevo)
3. Menú hamburguesa → **APIs y servicios** → **Credenciales**

### Obtener la API Key (`YOUTUBE_API_KEY`):

1. Si ya tienes una API Key (empieza por `AIza...`), cópiala
2. Si no: haz clic en **Crear credenciales** → **Clave de API** → cópiala
3. **IMPORTANTE:** La clave debe empezar por `AIza`. Si empieza por otra cosa, no es una API Key válida.

### Activar la API de YouTube (si no está):

1. En Google Cloud Console → **APIs y servicios** → **Biblioteca**
2. Busca "YouTube Data API v3"
3. Haz clic en **Habilitar**

### Obtener el Channel ID (`YOUTUBE_CHANNEL_ID`):

**Opción A — Desde YouTube Studio:**
1. Abre https://studio.youtube.com
2. Abajo a la izquierda → **Configuración** → **Canal** → **Información básica**
3. Verás "ID del canal" → empieza por `UC...`

**Opción B — Desde la URL del canal:**
1. Abre tu canal de YouTube en el navegador
2. La URL será: `https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxx`
3. El código después de `/channel/` es tu Channel ID

### Renovación:

| Variable | Caduca | Cómo renovar |
|---|---|---|
| `YOUTUBE_API_KEY` | No | Solo si la revocas manualmente |
| `YOUTUBE_CHANNEL_ID` | No | Es un ID fijo |

---

## 5. Gemini (Google AI)

### Dónde ir:

1. Entra en https://aistudio.google.com/apikey
2. Haz clic en **"Create API Key"** (o copia una existente)
3. Ese es tu `GEMINI_API_KEY` (empieza por `AIza...`)

### Renovación:

No caduca salvo que la revoques manualmente.

---

## 6. Contraseña del panel

| Variable | Qué poner |
|---|---|
| `PANEL_PASSWORD` | La contraseña que tú quieras para proteger el acceso al panel. Invéntatela. |

### Renovación:

No caduca. Cámbiala cuando quieras editando el `.env` y los secrets de Streamlit Cloud.

---

## Checklist final

Cuando tengas todo, tu `.env` debería tener 17 líneas (una por variable), sin comillas, sin espacios extra:

```
DB_HOST=auth-db1501.hstgr.io
DB_USER=u764199979_admin
DB_PASSWORD=MiPassword123
DB_NAME=u764199979_rrss_analytics
INSTAGRAM_TOKEN=EAAGm0ZBqr9XIBOlargotokenaqui
INSTAGRAM_ACCOUNT_ID=17841405309462918
META_CLIENT_ID=904523187654321
META_CLIENT_SECRET=abc123def456ghi789
TIKTOK_ACCESS_TOKEN=act.tokendetiktok
TIKTOK_CLIENT_KEY=awx7clientkey
TIKTOK_CLIENT_SECRET=cS9clientsecret
TIKTOK_REFRESH_TOKEN=rft.refreshtoken
TIKTOK_REDIRECT_URI=https://localhost:3000/
YOUTUBE_API_KEY=AIzaSyBmiapikeyaqui
YOUTUBE_CHANNEL_ID=UCmicanalidaqui
GEMINI_API_KEY=AIzaSyDgeminikey
PANEL_PASSWORD=miClaveDelPanel
```

### Para ejecutar:

```bash
streamlit run app.py
```

### Para recargar todo el histórico:

```bash
python recargas_historico.py
```
