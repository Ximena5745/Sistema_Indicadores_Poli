Guía rápida: Despliegue en Streamlit Cloud

Resumen
- Este proyecto contiene una app basada en Streamlit localizada principalmente en `streamlit_app/`.
- Plantillas HTML embebibles y assets están en `streamlit_app/components/ui/templates/`.
- Las gráficas usan ECharts vía CDN en plantillas embebibles y Plotly en algunas páginas (ambas compatibles con Streamlit Cloud).

Requisitos (archivo)
- Asegúrate de tener un `requirements.txt` en la raíz con al menos:
  - streamlit
  - pandas
  - plotly
  - openpyxl
  - xlrd

Pasos para deploy en Streamlit Cloud
1. Subir el repo a GitHub (público o privado según política).
2. En https://share.streamlit.io crea una nueva app apuntando al repo y rama.
   - App file path: `streamlit_app/pages/cmi_estrategico.py` (o `app.py` si tu app principal lo define)
3. Environment
   - Streamlit instalará `requirements.txt` automáticamente.
   - Si usas archivos xlsx en `data/raw/`, subirlos al repo o configurar un storage externo accesible.
4. Variables de entorno / Secrets
   - Si necesitas claves o rutas (p. ej. API, S3), configúralas en Settings → Secrets.
5. Assets y performance
   - Actualmente ECharts se carga desde CDN (`jsdelivr`). Para entornos corporativos con restricciones, puedes bundle localmente los archivos JS y servirlos desde `streamlit_app/components/static/`.
6. Comprobaciones post-deploy
   - Verificar: carga de datos (`cargar_acciones_mejora()`), render de plantillas embebibles, y que `st.cache_data` funcione.

Notas técnicas y recomendaciones
- Evitar llamadas a recursos externos sin fallback; si el CDN no está disponible, la app debe degradar a una tabla textual.
- Usar `st.cache_data` para endpoints de carga de ficheros (ya implementado en `services/data_loader.py`).
- Para assets locales: incluirlos en el repo y referenciarlos vía relative path en los templates.

Ejecutar localmente (pruebas)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app/pages/cmi_estrategico.py
```

Checklist antes de push
- [ ] `requirements.txt` actualizado
- [ ] Archivos de datos necesarios incluidos o documentados
- [ ] `STREAMLIT_CLOUD_DEPLOY.md` añadido al repo
- [ ] Tests básicos pasan (opcional)

Contacto
- Si necesitas que prepare la configuración completa para Streamlit Cloud (archivo `.streamlit` o `Procfile`), dímelo y lo genero.
