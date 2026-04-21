# 🎨 Guía de Personalización - Paleta de Colores Azul

## Sistema de Variables CSS para Fácil Personalización

---

## 📍 Ubicación de Variables CSS

**Archivo**: `dashboard_profesional_v2.html`  
**Líneas**: 22-50 (dentro de `<style>`)  
**Selector**: `:root`

---

## 🔑 Variables CSS Disponibles

### 1. COLORES PRINCIPALES - Azul Corporativo

```css
:root {
    --primary: #0c63e4;              /* Azul principal - Botones, títulos */
    --primary-light: #3b82f6;        /* Azul claro - Fondos suaves */
    --primary-dark: #0550c8;         /* Azul oscuro - Hover/Active */
    --primary-lighter: #e0f4ff;      /* Azul ultra claro - Fondos */
    
    --secondary: #0ea5e9;            /* Azul Cyan - Contraste secundario */
    --secondary-light: #7dd3fc;      /* Azul Cyan claro */
    --tertiary: #6366f1;             /* Azul Indigo - Variación */
}
```

### 2. COLORES SEMÁNTICOS - No Cambiar

```css
:root {
    --warning: #f59e0b;              /* Naranja - Alertas */
    --danger: #ef4444;               /* Rojo - Crítico */
    --success: #10b981;              /* Verde - Cumplido */
}
```

### 3. COLORES DE LÍNEAS - Paleta Gráficos

```css
:root {
    --line-1: #0c63e4;      /* Azul principal */
    --line-2: #0ea5e9;      /* Azul Cyan */
    --line-3: #6366f1;      /* Azul Indigo */
    --line-4: #0550c8;      /* Azul oscuro */
    --line-5: #3b82f6;      /* Azul claro */
    --line-6: #06b6d4;      /* Cyan */
}
```

### 4. FONDOS Y GRISES

```css
:root {
    --bg-light: #f7fafc;             /* Fondo claro (casi blanco) */
    --bg-lighter: #eef5ff;           /* Fondo azul muy claro */
    --bg-dark: #0f172a;              /* Para dark mode */
    
    --border-color: #cbd5e1;         /* Borde gris-azulado */
    --info-light: #dbeafe;           /* Azul info muy claro */
}
```

### 5. TIPOGRAFÍA

```css
:root {
    --text-dark: #1e293b;            /* Texto principal */
    --text-light: #64748b;           /* Texto secundario */
    --text-muted: #94a3b8;           /* Texto deshabilitado */
}
```

---

## 🎯 Cómo Cambiar la Paleta de Colores

### Método 1: Cambiar Variables CSS (Recomendado)

**Paso 1**: Abrir archivo en editor
```bash
code dashboard_profesional_v2.html
```

**Paso 2**: Ir a línea 22 (`:root {`)

**Paso 3**: Cambiar valores. Ejemplo: Tonos más claros

```css
:root {
    --primary: #3b82f6;              /* Más claro */
    --primary-light: #60a5fa;
    --primary-dark: #1e40af;
    --secondary: #7dd3fc;
    --tertiary: #818cf8;
}
```

**Paso 4**: Guardar (Ctrl+S)

**Paso 5**: Recargar navegador (F5)

### Método 2: Tonos Más Oscuros (Corporativo)

```css
--primary: #0550c8;                  /* Más formal */
--primary-light: #0c63e4;
--primary-dark: #0338a6;
--secondary: #0284c7;                /* Azul profundo */
```

### Método 3: Tonos Más Claros (Moderno)

```css
--primary: #3b82f6;                  /* Más amigable */
--primary-light: #60a5fa;
--primary-dark: #1e40af;
--secondary: #38bdf8;                /* Cyan claro */
```

---

## 🔄 Partes que se Actualizan Automáticamente

Cuando cambias una variable CSS, se actualiza automáticamente en:

| Elemento | Variable | Efecto |
|----------|----------|--------|
| **Sidebar** | `--primary-dark`, `--primary` | Degradado del menu |
| **Botones** | `--primary` | Color de acción |
| **Gráficos Chart.js** | `--line-1` a `--line-6` | Colores de barras/líneas |
| **Gráficos ECharts** | Interpoladas en gradientes | Todas las visualizaciones |
| **Iconos** | `--primary` | Tono de iconografía |
| **Hover states** | `--primary-light` | Efectos de interacción |
| **Bordes** | `--border-color` | Divisiones entre elementos |

---

## 🎨 Presets de Paletas Predefinidas

### Preset 1: Azul Corporativo Profesional ⭐ (ACTUAL)

```css
--primary: #0c63e4;
--secondary: #0ea5e9;
--tertiary: #6366f1;
```

**Uso**: Instituciones, finanzas, gobierno  
**Apariencia**: Formal, confiable, profesional

---

### Preset 2: Azul Moderno SaaS

```css
--primary: #3b82f6;
--secondary: #38bdf8;
--tertiary: #0ea5e9;
```

**Uso**: Tech startups, SaaS  
**Apariencia**: Moderno, accesible, dinámico

---

### Preset 3: Azul Académico Tradicional

```css
--primary: #0550c8;
--secondary: #1e40af;
--tertiary: #0338a6;
```

**Uso**: Universidades, educación  
**Apariencia**: Solemne, académico, establecido

---

### Preset 4: Gradiente Azul Turquesa (Innovador)

```css
--primary: #0891b2;
--secondary: #06b6d4;
--tertiary: #0284c7;
```

**Uso**: Tecnología, innovación  
**Apariencia**: Fresco, contemporáneo, dinámico

---

## 🔧 Modificaciones Avanzadas por Elemento

### Cambiar Solo el Sidebar

Buscar:
```css
.sidebar {
    background: linear-gradient(135deg, #0550c8 0%, #0c63e4 50%, #0ea5e9 100%);
}
```

Cambiar a:
```css
.sidebar {
    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 50%, var(--secondary) 100%);
}
```

### Cambiar Hero Section

```css
.hero-section {
    background: linear-gradient(135deg, #0550c8 0%, #0c63e4 30%, #0ea5e9 70%, #7dd3fc 100%);
}
```

### Cambiar Sombras

Buscar cualquier `rgba(12, 99, 228` y reemplazar con tus colores RGB:

```css
/* Extraer RGB de tu color hex */
#0c63e4 = RGB(12, 99, 228)
box-shadow: 0 10px 40px rgba(12, 99, 228, 0.3);
```

---

## 📊 Impacto Visual de Cambios

### Cambio de `--primary`

- Afecta: Botones, iconos, títulos, acentos
- Visibilidad: MUY ALTO
- Recomendación: Hacer cambios principales aquí

### Cambio de `--secondary`

- Afecta: Gráficos, hover effects
- Visibilidad: ALTO
- Recomendación: Usar para contraste

### Cambio de `--border-color`

- Afecta: Divisiones, cards, tablas
- Visibilidad: MEDIO
- Recomendación: Mantener coherente con `--bg-lighter`

---

## ✅ Checklist: Validar Cambios de Paleta

- [ ] Sidebar se ve coherente
- [ ] Botones tienen buen contraste
- [ ] Gráficos se ven profesionales
- [ ] Tablas son legibles
- [ ] Hover effects son evidentes
- [ ] Dark elements distinguibles
- [ ] Bordes visibles pero sutiles
- [ ] Tipografía contrasta bien

---

## 🎓 Ejemplo: Cambiar a Paleta Verde

**Si quisieras verde en lugar de azul:**

```css
:root {
    --primary: #059669;              /* Verde esmeralda */
    --primary-light: #10b981;        /* Verde claro */
    --primary-dark: #047857;         /* Verde oscuro */
    --secondary: #34d399;            /* Verde menta */
    --tertiary: #6ee7b7;             /* Verde claro */
}
```

**Pero mantener**:
```css
--warning: #f59e0b;
--danger: #ef4444;
--success: #10b981;  /* ← O cambiar a otro verde */
```

---

## 🔐 Mejores Prácticas

1. **Nunca cambiar valores RGBA en líneas individuales**
   - Usar variables CSS en su lugar
   - Ejemplo: `rgba(var(--primary-rgb), 0.2)`

2. **Mantener contraste mínimo 4.5:1**
   - Verificar con: https://webaim.org/resources/contrastchecker/

3. **Probar en todos los tabs**
   - Verificar que cambios se reflejan en: Inicio, Estrategia, Operación

4. **Documentar cambios**
   - Actualizar MEJORAS_DASHBOARD_v2.md con la paleta nueva

---

## 🧪 Testing Visual

```html
<!-- Copiar en consola del navegador para ver cambios en vivo -->
<script>
  // Cambiar a verde temporalmente
  document.documentElement.style.setProperty('--primary', '#059669');
  document.documentElement.style.setProperty('--secondary', '#34d399');
  
  // Volver al azul
  document.documentElement.style.setProperty('--primary', '#0c63e4');
  document.documentElement.style.setProperty('--secondary', '#0ea5e9');
</script>
```

---

## 📞 Soporte

Si necesitas:
- **Cambiar la paleta**: Usa variables CSS `:root`
- **Ajustar gráficos específicos**: Busca `color:` en datos.js
- **Cambiar fuentes**: Busca `font-family` en estilos

---

**Última actualización**: 20 Abril 2026  
**Sistema de colores**: Azul Profesional v2.0  
**Estado**: Producción ✅
