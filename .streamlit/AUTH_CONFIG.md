# Autenticación OIDC - Microsoft Entra ID

## Quick Start

### 1. Proteger la página principal
La página `streamlit_app/app.py` ya está protegida automáticamente.

### 2. Proteger páginas adicionales
Agrega este import al **inicio** de cada archivo en `streamlit_app/pages/`:

```python
# Al inicio de cada página
from pages.auth_guard import require_page_auth
require_page_auth()
```

### 3. Configurar secrets en Streamlit Cloud
Ver `secrets_ejemplo.toml` para el formato completo.

---

## Configuración de Microsoft Entra ID

### Paso 1: Registrar aplicación

1. Ve a [Microsoft Entra Portal](https://entra.microsoft.com/)
2. Selecciona **Registros de aplicaciones** → **Nuevo registro**
3. Configura:
   - Nombre: `Sistema de Indicadores Poli`
   - Tipos de cuenta compatibles: **Solo cuentas de esta organización** (single tenant)
   - URI de redirección: Selecciona **Web**
   ```
   https://tu-app.on.streamlit.io/api/auth/callback
   ```

### Paso 2: Obtener Client ID

1. Una vez creada la app, verás el **Application (client) ID**
2. Copia este valor → es tu `client_id` en los secrets

### Paso 3: Crear Client Secret

1. En tu app registrada, ve a **Certificados y secretos** → **Nuevo secreto de cliente**
2. Descripción: `Streamlit Production`
3. Expiración: **24 meses** (recomendado)
4. **COPIA EL VALOR INMEDIATAMENTE** (se oculta al recargar)
5. Este es tu `client_secret` en los secrets

### Paso 4: Configurar Authentication

1. Ve a **Autenticación** → **Agregar una plataforma** → **Web**
2. URI de redirección:
   ```
   https://tu-app.on.streamlit.io/api/auth/callback
   ```
3. En **Concesión de tokens**, marca:
   - ✅ Tokens de acceso
   - ✅ Tokens de ID

### Paso 5: Configurar permisos de API

1. Ve a **Permisos de API** → **Agregar un permiso**
2. Selecciona **Microsoft Graph** → **Permisos delegados**
3. Agrega:
   - ✅ `openid` - Iniciar sesión
   - ✅ `profile` - Ver perfil básico
   - ✅ `email` - Ver dirección de correo
4. Clic en **Otorgar consentimiento de administrador** (si tienes permisos)

### Paso 6: Configurar API Token

1. Ve a **Exposición de API** → **Agregar un ámbito**
2. Nombre del ámbito: `access_as_user`
3. ¿Quién puede dar consentimiento?: **Usuarios**
4. Permisos incluidos: `openid`, `profile`, `email`

### Paso 7: Obtener Tenant ID

1. En la página de tu app, busca **Directory (tenant) ID**
2. Tu client_id está configurado correctamente

---

## Estructura de Secrets

```toml
# Autenticación Microsoft Entra ID
auth_provider = "microsoft"
client_id = "TU_APPLICATION_ID"           # from "Application (client) ID"
client_secret = "TU_CLIENT_SECRET"        # from "Certificates and secrets"
require_email_verified = true

# Allowlist - todos los correos @poligran.edu.co
allowed_emails = [
    "admin@poligran.edu.co",
    "director@poligran.edu.co",
]
```

---

## Solución de Problemas

### "redirect_uri_mismatch"
- El URI en Entra no coincide exactamente con tu URL de Streamlit
- Copia exactamente: `https://TU-APP.on.streamlit.io/api/auth/callback`

### "AADSTS50011: The reply URL"
- Verifica que el redirect URI en Azure coincida exactamente

### "Not whitelisted"
- Tu correo no está en `allowed_emails`
- Verifica que uses **minúsculas** en los correos

### "AADSTS700016: Application not found"
- El `client_id` es incorrecto o la app no existe
- Verifica el Application (client) ID en Azure

### "AADSTS70002: Invalid credentials"
- El `client_secret` está mal o expiró
- Crea un nuevo secret en "Certificates and secrets"

---

## Notas de Seguridad

1. **NUNCA** expongas `client_secret` en código fuente
2. **NUNCA** imprimas `st.secrets` ni tokens en logs
3. **ROTA** los secrets cada 12-24 meses
4. **USA** allowlist para limitar acceso solo a `@poligran.edu.co`
5. **HABILITA** `email_verified = true` en producción

---

## URLs de tu app

Reemplaza `tu-app` con el nombre de tu aplicación en Streamlit:

- **Redirect URI**: `https://tu-app.on.streamlit.io/api/auth/callback`
- **URL de la app**: `https://tu-app.on.streamlit.io`