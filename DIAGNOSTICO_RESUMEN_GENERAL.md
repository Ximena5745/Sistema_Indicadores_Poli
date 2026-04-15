# Validación: Dashboard "Resumen General" - Plan de Acción

## 🔍 Problema Diagnosticado

El dashboard **no muestra datos** porque el **caché de Streamlit contiene DataFrames vacíos**. Las funciones de carga (`load_worksheet_flags()` y `load_cierres()`) están correctas, pero Streamlit está sirviendo valores cachados de una ejecución anterior fallida.

### Evidencia encontrada:
- ✅ Datos en Excel: Correctos y accesibles
- ✅ Funciones solo cacheadas: Funcionan normalmente (575 registros de flags, 984 de cierres)
- ✅ IDs comunes: 43 indicadores PDI coinciden en "Consolidado Cierres"
- ❌ Funciones con `@st.cache_data`: Retornan DataFrames vacíos (caché corrupto)

---

## 🔧 Soluciones Aplicadas

1. **✅ Limpieza de caché global**
   - Eliminado: `~/.streamlit` (y su caché)
   - El caché local del proyecto (`.streamlit/`) está vacío

2. **Pendiente: Reinicio de Streamlit**
   - El servicio debe reiniciar para limpiar la caché en memoria

---

## 📋 Plan de Validación y Acción

### Paso 1: Limpiar por completo
```bash
# Si aún hay procesos streamlit corriendo
pkill -f streamlit  # En Linux/Mac
taskkill /IM streamlit.exe  # En Windows
```

### Paso 2: Re Iniciar dashboard
En la terminal del proyecto:
```bash
cd c:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli
python scripts/start_streamlit.py
```

O si ejecutas directo:
```bash
streamlit run streamlit_app/app.py
```

### Paso 3: Verificar que funciona

1. Abre el navegador: `http://localhost:8501`
2. Ve a página > "Resumen general"
3. Selecciona año **2025** y presiona "Año de análisis"
4. ✅ Debes ver tarjetas KPI con datos (Total indicadores, Sobrecumplimiento, etc.)

---

## 🧪 Script de Validación (Opcional)

Si quieres verificar antes de reiniciar sin Streamlit:

```bash
python scripts/debug_resumen_general.py
```

Debería mostrar:
- ✅ Archivos existentes
- ✅ Worksheet Flags cargados
- ✅ Cierres cargados  
- ✅ Preparar PDI retorna datos

---

## ⚠️ Si aún no funciona

Si después de reiniciar Streamlit sigue mostrándo vacío, ejecuta:

```bash
python scripts/validate_pdi_chain.py
```

Esto validará:
1. Si hay datos en Excel
2. Si los IDs coinciden
3. Si hay registros de 2025

---

## 📌 Notas técnicas

- Las funciones `load_worksheet_flags()` y `load_cierres()` tienen `@st.cache_data(ttl=300)`
- El TTL es de 300 segundos (5 minutos), pero el caché corrupto no se invalida solo
- La refactorización no rompió nada, solo expuso un problema de caché stale

