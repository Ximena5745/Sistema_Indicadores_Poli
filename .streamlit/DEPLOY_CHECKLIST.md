# Checklist de Despliegue - Autenticación Streamlit

## ✅ Pre-Despliegue

- [ ] Streamlit 1.35+ en requirements.txt
- [ ] `.streamlit/secrets.toml` NO está en Git (verificar .gitignore)
- [ ] `.gitignore` incluye `.streamlit/secrets.toml`

## ✅ Configuración de Secrets en Streamlit Cloud

- [ ] `auth_provider = "microsoft"`
- [ ] `client_id` configurado correctamente
- [ ] `client_secret` configurado (NO en código)
- [ ] `allowed_emails` contiene los correos autorizados (minúsculas)
- [ ] `require_email_verified` establecido (recomendado: true)

## ✅ Proveedor OIDC

- [ ] Google: OAuth consent screen configurado, usuarios de prueba agregados
- [ ] Microsoft: App registration creada, permisos de API configurados
- [ ] Redirect URI coincide exactamente: `https://TU-APP.on.streamlit.io/api/auth/callback`

## ✅ Seguridad

- [ ] NO hay prints de st.secrets en código
- [ ] NO hay logging de tokens o client_secret
- [ ] Allowlist configurada (no hardcodeada)
- [ ] `require_email_verified = true` en producción
- [ ] Client secret tiene expiración configurada en el proveedor

## ✅ Testing Local

```bash
# Probar localmente con secrets de desarrollo
streamlit run streamlit_app/app.py
```

## ✅ Verificación Post-Despliegue

- [ ] Login funciona correctamente
- [ ] Usuario autorizado puede acceder
- [ ] Usuario no autorizado recibe mensaje de acceso denegado
- [ ] Botón logout funciona
- [ ] No hay errores en DevTools console

---

## 📁 Estructura de Archivos

```
.
├── .streamlit/
│   ├── config.toml          # Configuración de Streamlit
│   ├── secrets_ejemplo.toml # Ejemplo (NO usar en prod)
│   ├── AUTH_CONFIG.md       # Guía de configuración OIDC
│   └── DEPLOY_CHECKLIST.md  # Este archivo
├── streamlit_app/
│   ├── auth.py              # Módulo de autenticación
│   ├── app.py              # App principal (modificado)
│   └── ...
└── .gitignore              # Debe incluir .streamlit/secrets.toml
```

---

## 🚀 Despliegue Rápido

1. Configurar OAuth en Google/Microsoft
2. Copiar secrets a Streamlit Cloud
3. Hacer push a GitHub
4. Streamlit detectará automáticamente

```toml
# Secrets en Streamlit Cloud (Settings → Secrets)
auth_provider = "microsoft"
client_id = "TU_APPLICATION_ID"
client_secret = "TU_CLIENT_SECRET"
require_email_verified = true
allowed_emails = [
    "admin@poligran.edu.co",
    "director@poligran.edu.co",
]
```

---

## ❓ Preguntas Frecuentes

**P: Puedo usar autenticación sin configurar Microsoft Entra ID?**
R: No, st.login() requiere un provider OAuth configurado.

**P: Cómo pruebo localmente?**
R: Crea un `.streamlit/secrets.toml` local con las credenciales de tu app registrada en Azure.

**P: El login no funciona, qué revisar?**
R: Verifica que el redirect URI en Azure coincida exactamente con tu URL de Streamlit.

**P: Puedo agregar correos de otros dominios?**
R: Solo agrega los correos específicos a `allowed_emails`. Para este proyecto, solo @poligran.edu.co.

**P: El client_secret expiró?**
R: Ve a Microsoft Entra → Certificados y secretos → Crea uno nuevo y actualiza en Streamlit Cloud.