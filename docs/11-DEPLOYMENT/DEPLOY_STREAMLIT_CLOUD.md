# Despliegue en Streamlit Cloud

Esta guía detalla los pasos para desplegar la aplicación `streamlit_app/main.py` en Streamlit Cloud.

Requisitos previos
- Cuenta de GitHub con el repositorio del proyecto push-eado.
- Acceso a Streamlit Cloud (https://share.streamlit.io) con la cuenta de GitHub conectada.
- `requirements.txt` actualizado en la raíz del repo (ya existe).

Pasos rápidos
1. Asegúrate de que el repositorio esté en GitHub y contenga los siguientes archivos en la rama que desplegarás:
   - `streamlit_app/main.py` (entrypoint)
   - `requirements.txt`
   - `.streamlit/config.toml` (tema y ajustes server) — ya incluido.
2. Entra a https://share.streamlit.io y presiona "New app" → conecta tu repositorio GitHub → selecciona la rama y la ruta de la app: `streamlit_app/main.py` → Deploy.

Ajustes importantes en Streamlit Cloud
- Environment/Secrets: en la página del app, abre "Settings" → "Secrets" y añade variables como:
  - `DATABASE_URL`, `KAWAK_API_KEY`, `SOME_PASSWORD`, etc.
- Advanced options: no es obligatorio, pero puedes seleccionar una imagen más grande si la app necesita más memoria/CPU.

Comprobaciones post-despliegue
- Revisar logs en la página de la app (tab "Logs") si falla la instalación de paquetes o si faltan dependencias.
- Si la app requiere archivos grandes (Excel, DB), súbelos a un almacenamiento accesible (S3, Google Drive con accesos) y configura las variables de entorno.

Recomendaciones de producción
- Mover credenciales y secretos a Streamlit Cloud Secrets; nunca commit en texto plano.
- Evitar dependencias no necesarias en `requirements.txt` para reducir tiempo de arranque.
- Si hay tareas periódicas (ETL), programarlas fuera de Streamlit (Cloud Scheduler / GitHub Actions) y exponer resultados a la app.

Comandos útiles (local)
```bash
# Inicializar repo local, commit y push
git init
git add .
git commit -m "Prepare for Streamlit Cloud deploy: theme, custom sidebar"
git remote add origin git@github.com:<tu_usuario>/<tu_repo>.git
git push -u origin main

# Ejecutar la app localmente para comprobar
streamlit run streamlit_app/main.py
```

Si quieres, puedo:
- crear el repositorio remoto (necesitaría credenciales o token), o
- ejecutar `streamlit run streamlit_app/main.py` aquí para comprobar visual, o
- ayudarte a añadir los Secrets recomendados desde la lista de variables que use la app.
