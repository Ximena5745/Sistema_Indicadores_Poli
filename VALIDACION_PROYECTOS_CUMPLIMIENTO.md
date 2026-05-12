# VALIDACIÓN: PROYECTOS Y CUMPLIMIENTO - ANÁLISIS FUNCIONAL

**Fecha:** 11 de mayo de 2026  
**Status:** 🔴 CRÍTICO - Desalineamiento código vs documentación  
**Severidad:** ALTA - Datos incorrectos en dashboard  

---

## 1. QUÉ DICE LA DOCUMENTACIÓN OFICIAL

### 1.1 Modelo de Datos (03_Modelo_Datos.md)

**CONSOLIDADO CIERRES — para proyectos institucionales:**

```
Hoja: Consolidado Cierres

Propósito: Cierres semestrales + Proyectos institucionales
Uso: resumen_general.py, cmi_estrategico.py
Identificación: Proyectos se marcan con flag Proyecto == 1 
                en Indicadores por CMI.xlsx

Campos:
  - Id: Identificador del proyecto/indicador
  - Indicador: Nombre del proyecto
  - Línea: Línea estratégica 
  - Objetivo: Objetivo estratégico
  - Año: Año del registro
  - Mes: Mes del registro
  - Meta: Meta del proyecto
  - Ejecución: Ejecución real
  - cumplimiento_pct: Porcentaje calculado
```

**INDICADORES POR CMI (Fuente de enriquecimiento):**

```
Campo: Proyecto (binario: 0/1)
Uso: Marcar qué indicadores son proyectos
Función: Clasificar registros de cierres como proyectos

IDs en CMI: 1, 2, 3, ..., 44 (números pequeños)
Nombres: "Innovación curricular", "Plan Talento", etc.
```

### 1.2 Dashboard (04_Dashboard.md)

```
Página: Resumen General
Fuente: Consolidado Cierres

Filtros: Año, Período
Vistas: 4 categorías - Indicadores, Proyectos, Retos, Consolidado
Vista "Proyectos": Muestra registros del consolidado filtrados como Proyecto=1
```

### 1.3 Lógica de Indicadores (02_Logica_Indicadores.md)

```
Fórmula de Cumplimiento:
  cumplimiento = ejecución / meta    (indicadores positivos)
  
Umbrales para Categorización:
  < 80%:      Peligro (Rojo)
  80-99%:     Alerta (Amarillo)  
  100-104%:   Cumplimiento (Verde)
  ≥ 105%:     Sobrecumplimiento (Azul)

REGLA: Todos los indicadores/proyectos ACTIVOS en el período
       tienen cumplimiento_pct calculado (nunca NULL)
```

---

## 2. QUÉ SUCEDE EN EL CÓDIGO ACTUAL

### 2.1 Intención Original (correcta)

```python
# streamlit_app/pages/resumen_general.py línea 100

def _get_proyectos_ids():
    """Retorna set de IDs de indicadores marcados como Proyecto==1 
       en CMI xlsx"""
    from services.cmi_filters import load_cmi_worksheet
    df = load_cmi_worksheet()
    
    # OBTIENE: IDs del worksheet (1, 2, 3, ... 44)
    return set(str(int(x)) if isinstance(x, float) else str(x).strip() 
               for x in df.loc[df["Proyecto"] == 1, "Id"].dropna())
```

### 2.2 Problema: ID Mismatch

**IDs en Worksheet (CMI):**
```
1, 2, 3, 4, 10, 10.1, 11, 12, 13, 13.1, ... 44
Nombres: "Innovación curricular", "Plan Talento", "Nuevo POLISIGS"
Cantidad: 44
```

**IDs en Consolidado Cierres (source data):**
```
68, 69, 100, 104, 106, 108, 109, ... 
Nombres: "Evaluación de desempeño", "Oportunidad respuesta", ...
Cantidad: 390 únicos
```

**RESULTADO:** 0 coincidencias → 0 proyectos mostrados en UI ❌

### 2.3 Raíz del Problema

El código asume:
> "Los IDs de proyectos en worksheet coinciden con IDs en cierres"

**LA REALIDAD:**
> Son dos sistemas completamente diferentes
> El worksheet (CMI) es clasificación estratégica
> Los cierres son registros operacionales consolidados

---

## 3. ANÁLISIS DE DATOS REAL

### 3.1 Auditoria de AUDIT1_Data_Source_Audit_20260509.md

**FUENTE 4: Indicadores por CMI**
```
Contrato: ⚠️ PARCIAL en data_contracts.yaml
Campo: Proyecto (presente)
Uso: Determinar qué indicadores son proyectos
Impacto: ALTO - afecta categorización en dashboard
```

**FUENTE 2: Consolidado Cierres**
```
Propósito: Cierres semestrales + Proyectos
Hojas: Consolidado Semestral, Histórico, CIERRES, Catálogo
Campos: Id, Indicador, Año, Mes, Meta, Ejecución, cumplimiento_pct
```

### 3.2 Lo que Sucede Realmente

1. **Consolidado Cierres** contiene registros de seguimiento
2. Estos tienen **cumplimiento_pct ya calculado**
3. El flag **Proyecto=1** en CMI es **METADATOS** de clasificación
4. La conexión debería ser: **Por Indicador (nombre)** no por ID

---

## 4. SOLUCIÓN ARQUITECTÓNICA

### 4.1 Opción A: Cambiar a Clasificación por Indicador ✅ RECOMENDADA

```python
# NUEVA LÓGICA EN resumen_general.py

elif category == "Proyectos":
    # Cargar DIRECTAMENTE los proyectos del worksheet
    base = load_worksheet_flags()
    pdi_estrategico = base[base["Proyecto"] == 1].copy()  # 44 proyectos
    
    # Enriquecer con cumplimiento desde indicadores del CMI
    if not pdi_estrategico.empty:
        # Cargar indicadores CMI que estén asociados a estos proyectos
        cmi_df = load_cmi_worksheet()
        cmi_proyectos = cmi_df[cmi_df["Proyecto"] == 1].copy()
        
        # Merge: Los proyectos YA tienen su info (Línea, Objetivo)
        # Cumplimiento viene de campo calculado si existe
        if "cumplimiento_pct" in cmi_proyectos.columns:
            pdi_estrategico = pdi_estrategico.merge(
                cmi_proyectos[["Id", "cumplimiento_pct", "Nivel de cumplimiento"]],
                on="Id",
                how="left"
            )
        
        # Fill missing cumplimiento
        pdi_estrategico["cumplimiento_pct"] = pdi_estrategico["cumplimiento_pct"].fillna(0)
```

### 4.2 Opción B: Enriquecer cierres en origen (ETL)

```python
# En el pipeline ETL (scripts/actualizar_consolidado.py):
# AGREGAR CAMPO: proyecto_clasificacion

def preparar_cierres():
    cierres = load_consolidado_cierres()
    cmi = load_cmi_worksheet()
    
    # Mapear proyecto flag
    proyecto_map = dict(
        cmi[["Id", "Proyecto"]].drop_duplicates()
    )
    
    cierres["Es_Proyecto"] = cierres["Id"].map(proyecto_map)
    # Ahora cierres tiene flag "Es_Proyecto=1"
    
    return cierres

# Uso en dashboard:
# pdi_estrategico = cierres[cierres["Es_Proyecto"] == 1]
```

---

## 5. VERIFICACIÓN DOCUMENTAL

### Reglas según PROJECT_RULES.md

| Regla | Estado | Acción |
|-------|--------|--------|
| **2.2** - No modificar lógica sin validar | ❌ VIOLADA | El código cambia filtrado de proyectos sin criterio |
| **2.1** - Reutilizar lógica existente | ⚠️ PARCIAL | Hay funciones duplicadas de normalización |
| **1** - Revisar contexto primero | ❌ FALLÓ | No se validó mapping de IDs previamente |

### Reglas según documentación funcional

| Requisito | Esperado | Actual | Cumple |
|-----------|----------|--------|--------|
| Proyectos activos en año muestran cumplimiento | Sí | No → 0 | ❌ |
| Cumplimiento calculado para cada proyecto | Sí | NULL | ❌ |
| Proyectos filtrados por Proyecto=1 flag | Sí | Sí | ✅ |
| Enriquecimiento de Línea/Objetivo | Sí | Sí | ✅ |

---

## 6. VALIDACIÓN DE DATOS

### 6.1 Dataset Actual

```
Worksheet Proyectos: 44 registros
  - IDs: 1-44 (algunos decimales tipo 10.1, 13.1)
  - Ejemplos: Innovación curricular, Plan Talento, Nuevo POLISIGS
  - Tiene: Línea, Objetivo, cumplimiento_pct (algunos)

Cierres Totales: 985 registros
  - IDs: 68, 100, 104, ... 
  - Ejemplos: Evaluación proveedores, Respuesta solicitudes
  - Tiene: Meta, Ejecución, cumplimiento_pct (902 no-null)

Solapamiento de IDs: 0 exactos
  ↳ IDs worksheet: 1,2,3,4,10,10.1,11,12,13,13.1...
  ↳ IDs cierres: 100,104,106,108,109,110...
  ↳ Overlap: 0 items
```

### 6.2 Conclusión

**Los IDs NO pueden ser criterio de unión.**

---

## 7. RECOMENDACIÓN OFICIAL

### 7.1 Diagnóstico

❌ **CONFLICTO:** El código asume que proyectos en worksheet tienen registros en cierres con IDs coincidentes

**LA VERDAD:** Los proyectos están en worksheet CON cumplimiento ya calculado en la columna `cumplimiento_pct`

### 7.2 Remediación Requerida

**OPCIÓN A (Inmediata):** 
- Cargar proyectos del worksheet (Proyecto=1)
- Usar cumplimiento del campo `cumplimiento_pct` del worksheet
- NO filtrar cierres

**OPCIÓN B (Long-term):**
- Enriquecer Consolidado Cierres en ETL con flag "Es_Proyecto"
- Mantener esquema de IDs consistentes
- Actualizar docs

---

## 8. IMPACTO EN OTRAS PÁGINAS

| Página | Usa Proyectos | Afectada | Acción |
|--------|---------------|----------|--------|
| resumen_general.py | SÍ | ✅ | Corregir carga |
| cmi_estrategico.py | SÍ | ✅ | Revisar línea 1658 |
| tablero_operativo.py | SÍ | ✅ | Revisar línea 2337 |
| plan_mejoramiento.py | SÍ | ✅ | Revisar línea 2634 |

---

## 9. CONCLUSIÓN

**Estado Documentación:** ✅ Correcta, coherente, completa

**Estado Código:** ❌ Implementación incorrecta vs docs

**Datos:** ✅ Disponibles, con cumplimiento calculado

**Solución:** Cambiar lógica de filtrado para usar Proyecto=1 del worksheet, no IDs

**Prioridad:** 🔴 CRÍTICA - Usuarios no ven proyectos

---

## Evidencias

- scripts/_archived/tmp_debug/tmp_proyectos_diagnostic.py: Confirma 44 proyectos en worksheet, 0 en cierres por ID
- scripts/_archived/tmp_debug/tmp_ids_mismatch.py: Demuestra 0 overlap entre IDs
- AGENT1_Data_Source_Audit: Documenta fuentes oficiales
- 03_Modelo_Datos.md: Define uso de Consolidado Cierres
