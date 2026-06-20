# AGENT 9 Implementation Guide
**Software Intelligence Framework v1.0 — SGIND**  
**Especialista en Calidad de Código**

---

## Quick Start

### 1️⃣ Ejecutar Análisis Completo
```bash
cd /workspace
python scripts/agent9_code_quality.py
```

**Output:**
```
✓ 135 archivos Python encontrados
✓ 1098 funciones analizadas
✓ 78 hallazgos detectados
✓ Artefactos guardados en artifacts/
```

### 2️⃣ Revisar Reportes
```bash
# Reporte en Markdown
cat artifacts/AGENT9_CODE_QUALITY_*.md

# Métricas en JSON
cat artifacts/CODE_METRICS_*.json
```

### 3️⃣ Priorizar Hallazgos
- 🔴 **CRÍTICOS:** Duplicación (INMEDIATO)
- 🟠 **ALTOS:** Complejidad (Esta semana)
- 🟡 **MEDIOS:** Refactorización (Este mes)

---

## 7 Dimensiones de Auditoría

### 1. Duplicación de Código
**¿Qué detecta?**
- Funciones con nombres similares
- Lógica repetida sin centralización
- Copy-paste entre módulos

**Ejemplo hallazgo:**
```
CAQ-DUP-001 — Duplicación de Código
Archivos: core/calculos.py, core/semantica.py, generar_reporte.py
Símbolo: categorizar_cumplimiento (3 versiones)
Solución: Centralizar en core/semantica.py
```

### 2. Complejidad Ciclomática
**¿Qué detecta?**
- Funciones con >10 condiciones anidadas
- Métodos que hacen muchas cosas
- Código difícil de testear

**Métrica:** Radon Cyclomatic Complexity
```python
# Alto: 15 condiciones
if a:
    if b:
        if c:
            # ... etc
            
# Refactorizar a:
if not valid():
    return
handle_valid()
```

### 3. Acoplamiento Innecesario
**¿Qué detecta?**
- Imports circulares (A importa B, B importa A)
- Módulos fuertemente dependientes
- Funciones que pasan objetos complejos

### 4. Funciones Largas
**¿Qué detecta?**
- Funciones > 50 líneas (revisar)
- Funciones > 100 líneas (refactorizar urgente)
- Métodos con >5 parámetros

### 5. Centralización
**¿Qué detecta?**
- Umbrales hardcodeados en múltiples lugares
- Validaciones esparcidas
- Constantes definidas en varios archivos

**Ejemplo:**
```python
# ❌ Disperso
UMBRAL_PA = 0.95  # en core/config.py
UMBRAL_PA = 0.95  # en scripts/xxxx.py
UMBRAL = 95       # en services/yyyy.py

# ✅ Centralizado
# core/config.py
UMBRAL_PA = 0.95

# Usado en todos lados
from core.config import UMBRAL_PA
```

### 6. Modularización
**¿Qué detecta?**
- Módulos con responsabilidades mixtas
- Clases que hacen múltiples cosas
- Separación de capas deficiente

**Arquitectura objetivo:**
```
core/config.py       ← Configuración
core/semantica.py    ← Lógica pura
scripts/etl/         ← Orquestación
services/            ← Dominio
streamlit_app/       ← Presentación
```

### 7. Testing & Testabilidad
**¿Qué detecta?**
- Funciones difíciles de mockear
- Tests que testean múltiples cosas
- Lógica ligada a I/O

---

## Cómo Leer un Hallazgo

```markdown
CAQ-CMP-042 — Complejidad Ciclomática
- Ubicación: core/calculos.py:156
- Símbolo: recalcular_cumplimiento_faltante()
- Descripción: Complejidad: 15 (máximo: 10)
- Impacto: Función con excesivas ramificaciones
- Solución: Refactorizar en funciones más pequeñas
- Esfuerzo: 3.0 horas
```

**Campos:**
- **ID:** Identificador único (CAQ-XXX)
- **Severidad:** CRÍTICO | ALTO | MEDIO | BAJO
- **Ubicación:** archivo:línea
- **Símbolo:** nombre de función/clase
- **Descripción:** ¿Cuál es el problema?
- **Impacto:** ¿Por qué importa?
- **Solución:** ¿Cómo lo arreglamos?
- **Esfuerzo:** Horas estimadas

---

## Flujo de Refactorización

### PASO 1: Priorizar
```
Ordenar por:
1. Severidad (CRÍTICO → BAJO)
2. Impacto (qué afecta más usuarios)
3. Esfuerzo (combinar altos/muchas horas)
```

### PASO 2: Analizar
```
Para cada hallazgo:
1. ¿Es realmente un problema?
2. ¿Hay dependencias?
3. ¿Hay tests para esto?
4. ¿Cuál es el plan exacto?
```

### PASO 3: Refactorizar
```
1. Crear rama: git checkout -b refactor/CAQ-XXX
2. Hacer cambios
3. Ejecutar tests: pytest
4. Validar AGENT 9 nuevamente
5. PR + Merge
```

### PASO 4: Validar
```
1. Reejecutar AGENT 9
2. ¿Desapareció el hallazgo?
3. ¿Nuevos hallazgos creados?
4. ¿Mejor cobertura de tests?
```

---

## Integración en CI/CD

### GitHub Actions
```yaml
# .github/workflows/code-quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  agent9:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Run AGENT 9
        run: python scripts/agent9_code_quality.py
      
      - name: Upload metrics
        uses: actions/upload-artifact@v2
        with:
          name: code-metrics
          path: artifacts/CODE_METRICS_*.json
      
      - name: Comment PR
        if: github.event_name == 'pull_request'
        run: |
          echo "Code Quality Report:" >> $GITHUB_STEP_SUMMARY
          cat artifacts/AGENT9_CODE_QUALITY_*.md >> $GITHUB_STEP_SUMMARY
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running AGENT 9..."
python scripts/agent9_code_quality.py

if [ $? -ne 0 ]; then
    echo "Code quality check failed"
    exit 1
fi
```

---

## Referencia Rápida

### Archivos Clave
```
.agent9.instructions.md          ← Prompt especializado
scripts/agent9_code_quality.py   ← Framework ejecutable
AGENT9_IMPLEMENTATION_REPORT.md  ← Este documento
```

### Artefactos Generados
```
artifacts/AGENT9_CODE_QUALITY_YYYYMMDD_HHMMSS.md  ← Hallazgos
artifacts/CODE_METRICS_YYYYMMDD_HHMMSS.json       ← Métricas
```

### Comandos Útiles
```bash
# Análisis completo
python scripts/agent9_code_quality.py

# Ver reporte
cat artifacts/AGENT9_CODE_QUALITY_*.md | less

# Ver métricas
python -m json.tool artifacts/CODE_METRICS_*.json | less

# Contar hallazgos
grep "^## " artifacts/AGENT9_CODE_QUALITY_*.md | wc -l

# Filtrar por severidad
grep "CRÍTICO\|ALTO" artifacts/AGENT9_CODE_QUALITY_*.md
```

---

## Mejores Prácticas

### ✅ DO's
- ✅ Refactorizar CRÍTICOS primero
- ✅ Ejecutar AGENT 9 después de cambios
- ✅ Testear antes de mergear
- ✅ Documentar por qué cambió
- ✅ Revisar con pares

### ❌ DON'Ts
- ❌ No ignorar hallazgos CRÍTICOS
- ❌ No refactorizar sin tests
- ❌ No hacer muchos cambios de una vez
- ❌ No confundir refactorización con reescritura
- ❌ No ignorar nuevos hallazgos después de cambios

---

## FAQ

**P: ¿Por qué 78 hallazgos?**  
A: Código maduro con ~1000 funciones. Número normal para migración hacia mejores prácticas.

**P: ¿Debo arreglar todos?**  
A: Prioriza CRÍTICOS (inmediato) + ALTOS (esta semana). Medios/Bajos pueden ser iterativos.

**P: ¿Cuánto tiempo toma?**  
A: ~75 horas distribuidas:
- CRÍTICOS: 5h
- ALTOS: 40h
- MEDIOS: 30h

**P: ¿AGENT 9 es perfecta?**  
A: No, es análisis estático. Revisa hallazgos antes de actuar.

**P: ¿Cómo lo integro en desarrollo?**  
A: Ejecuta después de cada commit, revisa antes de PR.

---

## Recursos Adicionales

- **Radon:** `pip install radon` → `radon cc -a -s .`
- **Pylint:** `pip install pylint` → `pylint .`
- **SonarQube:** Integración avanzada
- **Black:** Formateo automático
- **isort:** Organización de imports

---

**AGENT 9 — Code Quality & Refactoring Framework**  
**Versión:** 1.0 SGIND-Optimizada  
**Última actualización:** 9 de mayo de 2026
