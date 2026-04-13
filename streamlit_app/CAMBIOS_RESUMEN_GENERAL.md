# Cambio de Diseño - Resumen General

## 📋 Resumen del Cambio

El dashboard de **Resumen General** ha sido completamente rediseñado para eliminar la sobrecarga visual y mejorar la narrativa de datos.

## 🔄 Cambios Principales

### Lo que se ELIMINÓ:
- ❌ Tablas duplicadas "Por Nivel" y "Por Vicerrectoría"
- ❌ KPIs confusos con números sin contexto (287, 16, 24, 86, 120, 34)
- ❌ Alertas comparativas con IDs internos
- ❌ Filtros de año/mes separados
- ❌ Tablas de "Procesos con incremento de peligro"
- ❌ Matriz de calor y consolidados de cierres
- ❌ Múltiples gráficos redundantes

### Lo que se AÑADIÓ:
- ✅ **Dashboard HTML moderno y autocontenido** (`dashboard_estrategico.html`)
- ✅ **Filtro único de año** (2022-2025) que actualiza todos los datos dinámicamente
- ✅ **Sección 1: Indicadores PDI - CMI Estratégico**
  - Gráfico de cascada circular con líneas y objetivos estratégicos
  - 5 tarjetas KPI claras (Total, Sobrecumplimiento, Cumplimiento, Alerta, Peligro)
  - Top 3 indicadores que mejoraron/desmejoraron vs histórico
  - Insights estratégicos generados dinámicamente
- ✅ **Sección 2: Indicadores por Proceso**
  - Total de indicadores por proceso
  - Gráfico de barras apiladas por nivel de cumplimiento
  - Top 3 procesos con mayor mejora
  - Procesos en alerta con empeoramiento
  - Insights operativos generados dinámicamente

## 🎨 Diseño

- **Moderno y responsive**: Se adapta a desktop, tablet y móvil
- **Paleta de colores estandarizada**:
  - Sobrecumplimiento: `#10B981` (verde intenso)
  - Cumplimiento: `#34D399` (verde claro)
  - Alerta: `#F59E0B` (ámbar)
  - Peligro: `#EF4444` (rojo)
- **Interactivo**: Tooltips en gráficos, hover effects
- **Librerías**: Chart.js (vía CDN)

## 📁 Archivos Modificados

1. **`streamlit_app/pages/resumen_general.py`**
   - Reemplazado completamente (2210 líneas → 75 líneas)
   - Ahora solo carga y muestra el dashboard HTML
   - Backup del original: `resumen_general_backup.py`

2. **`streamlit_app/dashboard_estrategico.html`** (NUEVO)
   - Dashboard completo autocontenido
   - ~900 líneas de HTML/CSS/JS
   - Datos mock para años 2022-2025

## 🚀 Cómo Usar

1. Iniciar la aplicación Streamlit:
   ```bash
   streamlit run streamlit_app/main.py
   ```

2. Hacer clic en **"Resumen general"** en el menú lateral

3. Seleccionar un año (2022-2025) en el filtro superior

4. Explorar las dos secciones principales:
   - **Indicadores PDI - CMI Estratégico**
   - **Indicadores por Proceso**

## 📊 Datos

Los datos son **mock/simulados** para demostración, pero:
- Son coherentes y realistas
- Varían por año (2022-2025)
- Los insights se generan dinámicamente según los datos mostrados
- El filtro de año actualiza TODOS los componentes

## 🔄 Próximamente

Para producción, se recomienda:
1. Conectar el dashboard a los datos reales del sistema
2. Reemplazar los datos mock con consultas a la base de datos
3. Mantener la lógica de insights dinámicos
4. Agregar exportación a PDF/Excel

## 📝 Notas Técnicas

- El dashboard HTML es **autocontenido** (no depende de archivos externos excepto Chart.js CDN)
- Altura del iframe: 2800px (ajustable según necesidad)
- Compatible con todos los navegadores modernos
- No requiere instalación de paquetes adicionales

---

**Fecha del cambio:** 13 de abril de 2026  
**Versión:** 2.0  
**Autor:** GitHub Copilot
