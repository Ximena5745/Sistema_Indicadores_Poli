# REMEDIATION CHECKLIST — AGENT 4 AUDITORIA

**Documento:** REMEDIATION_CHECKLIST_20260509.md  
**Relacionado:** AGENT_4_DESINCRONIZACIONES_20260509.md  
**Última Actualización:** 9 de mayo de 2026

---

## 🔴 PHASE 1: ALINEACIÓN CRÍTICA (Semana 1 — 9-13 mayo 2026)

### TAREA 1.1: Actualizar Estado del Proyecto

**Desincronización:** H1 — Fase del Proyecto  
**Owner:** Project Manager  
**Tiempo Estimado:** 15 minutos  
**Complejidad:** 🟢 TRIVIAL

#### Checklist
- [ ] Leer [README.md](README.md#L1-L10) línea 1-10
- [ ] Cambiar línea 4 de:
  ```
  **Estado:** ✓ **Fase 2 EN EJECUCIÓN** (Semana 2/8) — ✅ Refactorización Arquitectónica Sprint 1-2 Completada
  ```
  a:
  ```
  **Estado:** ✅ **PHASE 3 COMPLETADA** — 9 de mayo de 2026 | Auditoría + Resilencia ✅
  ```
- [ ] Referenciar [artifacts/PHASE_3_CONSOLIDADO_20260509.md](artifacts/PHASE_3_CONSOLIDADO_20260509.md)
- [ ] Actualizar todas menciones de "Fase 2" en README.md línea 15-30
- [ ] Revisar commit message: "AGENT_4: Actualizar estado proyecto a PHASE 3"

#### Verificación
```bash
# Verificar que README.md no contiene "Fase 2" excepto en notas históricas
grep -n "Fase 2" README.md  # NO debe encontrar (excepto en archive/)
grep -n "PHASE 3" README.md  # DEBE encontrar en línea 4
```

---

### TAREA 1.2: Refactorizar Función categorizar_cumplimiento()

**Desincronización:** H3 — Duplicación de Función  
**Owner:** Backend Developer  
**Tiempo Estimado:** 1-2 horas  
**Complejidad:** 🟠 MEDIA

#### Checklist
- [ ] Leer [core/semantica.py](core/semantica.py#L54): Entender función oficial
- [ ] Leer [core/calculos.py](core/calculos.py#L77): Verificar que delega correctamente
- [ ] Verificar [scripts/consolidation/core/utils.py](scripts/consolidation/core/utils.py#L201):
  - [ ] Está usando `calcular_cumplimiento()` paralelo
  - [ ] NO importa desde core/semantica
- [ ] Refactorizar scripts/consolidation/core/utils.py:
  ```python
  # ANTES:
  def calcular_cumplimiento(meta, ejec, sentido, tope=1.3):
      ...
  
  # DESPUÉS:
  from core.semantica import categorizar_cumplimiento
  # (o mantener como wrapper delegante)
  ```
- [ ] Crear test en [tests/](tests/):
  ```python
  def test_categorizar_cumplimiento_consistency():
      """Verifica que todas las funciones usen core/semantica"""
      assert categorizar_from_calculos == categorizar_from_semantica
      assert categorizar_from_consolidation == categorizar_from_semantica
  ```
- [ ] Ejecutar tests: `pytest tests/test_config.py -v`
- [ ] Revisar commit message: "AGENT_4: Consolidar categorizar_cumplimiento en core/semantica"

#### Verificación
```bash
# Debe haber exactamente UNA función official en core/semantica.py
grep -n "^def categorizar_cumplimiento" core/semantica.py  # 1 resultado
grep -n "^def categorizar_cumplimiento" core/calculos.py   # 1 resultado (wrapper)
grep -n "^def calcular_cumplimiento" scripts/consolidation/core/utils.py  # Debe importar
```

---

### TAREA 1.3: Documentar Dependencia consolidar_api.py

**Desincronización:** H5 — Dependencia Oculta  
**Owner:** Technical Writer  
**Tiempo Estimado:** 45 minutos  
**Complejidad:** 🟢 TRIVIAL

#### Checklist
- [ ] Actualizar [docs/core/01_Arquitectura.md](docs/core/01_Arquitectura.md#L30):
  - [ ] Agregar sección "2.2.1 Orden de Ejecución ETL"
  - [ ] Insertar diagrama con pasos:
    ```
    1. consolidar_api.py → data/raw/Fuentes Consolidadas/
    2. actualizar_consolidado.py → data/output/Resultados Consolidados.xlsx
    3. generar_reporte.py → reportes PDF/Excel
    ```
- [ ] Crear nuevo archivo [deploy/SECUENCIA_EJECUCION.md](deploy/SECUENCIA_EJECUCION.md):
  ```markdown
  # Secuencia de Ejecución ETL
  
  ## Orden obligatorio:
  
  ### Paso 1: Consolidación API
  bash
  python scripts/consolidar_api.py
  # Genera: data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx
  
  ### Paso 2: Consolidación y Cálculos
  bash
  python scripts/actualizar_consolidado.py
  # Genera: data/output/Resultados Consolidados.xlsx
  
  ### Paso 3: Reportería
  bash
  python scripts/generar_reporte.py
  # Genera: reportes PDF/Excel
  ```
- [ ] Actualizar docstring en [scripts/actualizar_consolidado.py](scripts/actualizar_consolidado.py#L1-L30)
  - [ ] Ya existe, solo asegurar que está visible en docs
- [ ] Revisar commit message: "AGENT_4: Documentar secuencia ETL consolidar_api → actualizar_consolidado"

#### Verificación
```bash
# Verificar que documentación menciona consolidar_api.py
grep -r "consolidar_api" docs/
# Debe encontrar referencias en 01_Arquitectura.md y deploy/SECUENCIA_EJECUCION.md
```

---

### TAREA 1.4: Auditoría Autenticación Streamlit

**Desincronización:** H4 — Autenticación Incompleta  
**Owner:** DevOps / Backend  
**Tiempo Estimado:** 1.5 horas  
**Complejidad:** 🟠 MEDIA

#### Checklist
- [ ] **VERIFICAR EN STREAMLIT CLOUD:**
  - Ir a https://share.streamlit.io → Tu App → Settings
  - [ ] ¿Está configurado `auth_provider = "microsoft"`?
  - [ ] ¿Están configurados `client_id`, `client_secret`?
  - [ ] ¿Están configurados `allowed_emails`?
  - [ ] ¿Está activo login? (Intenta acceder sin token)
- [ ] **ESTANDARIZAR NOMBRES EN REPO:**
  - [ ] Crear `.streamlit/secrets.toml.template`:
    ```toml
    # COPY THIS TO secrets.toml (never commit secrets.toml!)
    auth_provider = "microsoft"
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    ```
  - [ ] Eliminar `secrets_ejemplo.toml` si no es usado
  - [ ] Usar SOLO `secrets.toml.template`
- [ ] **ACTUALIZAR [.streamlit/AUTH_CONFIG.md](.streamlit/AUTH_CONFIG.md):**
  - [ ] Agregar sección "Verificación de Estado"
  - [ ] Documentar: "✅ Autenticación activa en Streamlit Cloud (verificado 9-may-2026)"
  - [ ] Documentar: "✅ Local testing: ejecutar `streamlit run streamlit_app/app.py`"
- [ ] **TESTING LOCAL:**
  - [ ] Crear [.streamlit/test_auth_local.sh](.streamlit/test_auth_local.sh):
    ```bash
    #!/bin/bash
    # Testing local auth (uses secrets.toml if present)
    streamlit run streamlit_app/app.py
    ```
  - [ ] Documento: "Abre http://localhost:8501, debe pedir login o estar protegida"
- [ ] Revisar commit message: "AGENT_4: Estandarizar configuración Streamlit auth"

#### Verificación
```bash
# Verificar archivos de configuración
ls -la .streamlit/
# Debe tener: config.toml, secrets.toml.template, AUTH_CONFIG.md, DEPLOY_CHECKLIST.md
# NO debe tener: secrets.toml (está en .gitignore), secrets_ejemplo.toml (renombrado)

# Verificar que app.py tiene autenticación
grep -n "require_auth" streamlit_app/app.py  # Debe encontrar
```

---

## 🟠 PHASE 2: ALINEACIÓN ESTRUCTURAL (Semana 2 — 16-20 mayo 2026)

### TAREA 2.1: Alinear GOVERNANCE.md con Estructura Real

**Desincronización:** H2 — Estructura de Documentación  
**Owner:** Architect + Technical Writer  
**Tiempo Estimado:** 1-4 horas (depende de opción)  
**Complejidad:** 🟠 MEDIA

#### Checklist (OPCIÓN A — RECOMENDADA: Actualizar GOVERNANCE.md)
- [ ] Leer [docs/GOVERNANCE.md](docs/GOVERNANCE.md#L35): Sección "ESTRUCTURA DE CARPETAS"
- [ ] Comparar con realidad:
  ```
  ✅ REAL:     docs/archive/, docs/core/, docs/diagrams/, docs/prototypes/, docs/sql/
  ❌ ESPERADO: 11 carpetas (00-ESTRATEGIA/, 01-ANALISIS/, etc.)
  ```
- [ ] Actualizar línea 35-75 en GOVERNANCE.md:
  ```markdown
  # 📂 ESTRUCTURA DE CARPETAS (SIMPLIFICADA)
  
  Después de aplicar MDV (Mínimo Conjunto Viable) en PHASE 3,
  la estructura fue simplificada de 11→7 carpetas:
  
  docs/
  ├── archive/          → Documentación histórica (FASE 1-2)
  ├── core/             → Arquitectura + diseño técnico (01_Arquitectura.md, 02_Logica.md, etc.)
  ├── diagrams/         → Diagramas y visualizaciones
  ├── prototypes/       → Prototipos y pruebas de concepto
  ├── sql/              → Scripts SQL y modelos de base de datos
  ├── GOVERNANCE.md     → Este archivo
  ├── PROPUESTA_DASHBOARD_EJECUTIVO.md
  └── README.md         → Índice centralizado
  ```
- [ ] Documentar DECISIÓN: "Simplificación fue intencional para reducción de deuda"
- [ ] Actualizar línea 43 (Políticas de Eliminación): aclarar que aplica a carpetas reales
- [ ] Revisar commit message: "AGENT_4: Actualizar GOVERNANCE.md — estructura simplificada MDV"

#### Checklist (OPCIÓN B — ALTERNATIVA: Refactorizar docs/)
- [ ] ⚠️ ADVERTENCIA: Esta opción es disruptiva, requiere mover 15+ archivos
- [ ] Solo si Architect decide que es mejor mantener 11 carpetas prescritas
- [ ] Tarea separada, requiere planning adicional

#### Verificación (OPCIÓN A)
```bash
# Verificar que GOVERNANCE.md describe estructura real
ls docs/ | wc -l  # Debe ser ~7
grep "archive" docs/GOVERNANCE.md  # Debe encontrar
grep "00-ESTRATEGIA" docs/GOVERNANCE.md  # DEBE NO encontrar (o estar en nota histórica)
```

---

### TAREA 2.2: Documentar scripts/consolidation/

**Desincronización:** H9 — Directorio Paralelo Huérfano  
**Owner:** Backend Developer  
**Tiempo Estimado:** 45 minutos  
**Complejidad:** 🟢 TRIVIAL

#### Checklist
- [ ] Entender propósito: ¿Qué es scripts/consolidation/?
  - [ ] Leer archivos: core/, etl/, *_*.py
  - [ ] ¿Es código deprecado?
  - [ ] ¿Es alternativa experimental?
  - [ ] ¿Se usa en algún pipeline?
- [ ] Si está deprecado:
  - [ ] Crear [scripts/consolidation/README.md](scripts/consolidation/README.md):
    ```markdown
    # ⚠️ DEPRECATED — scripts/consolidation/
    
    Este directorio contiene versión antigua del pipeline ETL.
    
    **Status:** DEPRECADO — No se usa en production
    **Reemplazo:** Usar `scripts/actualizar_consolidado.py` en su lugar
    **Motivo:** Refactorización PHASE 3 — consolidación de módulos
    
    Para nueva lógica ETL, ver: docs/core/01_Arquitectura.md
    ```
  - [ ] Mover a `docs/archive/consolidation_legacy/` (opcional)
- [ ] Si se usa en production:
  - [ ] Crear [scripts/consolidation/README.md](scripts/consolidation/README.md):
    ```markdown
    # scripts/consolidation/ — Pipeline ETL Alternativo
    
    Versión experimental del pipeline. Usado para: [DESCRIBIR CASO]
    
    **Status:** ACTIVO (experimental)
    **Cuando usar:** [DESCRIBIR CUÁNDO]
    **Responsable:** [NOMBRE]
    
    ## Módulos
    - core/utils.py: Utilidades de cálculo
    - ...
    ```
  - [ ] Documentar en [docs/core/01_Arquitectura.md](docs/core/01_Arquitectura.md): cuándo usar cada uno
- [ ] Revisar commit message: "AGENT_4: Documentar propósito de scripts/consolidation/"

#### Verificación
```bash
# Verificar que scripts/consolidation tiene README.md
ls scripts/consolidation/README.md  # DEBE existir
cat scripts/consolidation/README.md  # DEBE ser claro sobre status
```

---

### TAREA 2.3: Documentar Data Contracts Enforcement

**Desincronización:** H7 — Data Contracts No Enforzados  
**Owner:** Backend Developer  
**Tiempo Estimado:** 1 hora  
**Complejidad:** 🟡 MEDIA

#### Checklist
- [ ] Leer [config/data_contracts.yaml](config/data_contracts.yaml): ¿Qué reglas define?
- [ ] Leer [services/data_loader.py](services/data_loader.py): ¿Cuándo se valida?
- [ ] Crear sección en [docs/core/01_Arquitectura.md](docs/core/01_Arquitectura.md):
  ```markdown
  ## 2.5 Capa de Validación (Data Contracts)
  
  **Propósito:** Garantizar que datos cumplen reglas definidas en config/data_contracts.yaml
  
  **Dónde se ejecuta:**
  - services/data_loader.py: Al cargar datos (si skill está disponible)
  - scripts/actualizar_consolidado.py: Validación de entrada
  
  **Reglas definidas en:** config/data_contracts.yaml
  
  **Validaciones ejecutadas:**
  - [Listar aquí qué valida]
  ```
- [ ] Actualizar [PROJECT_RULES.md](project_rules.md#L130):
  - [ ] Agregar sección "2.4 Data Contracts"
  - [ ] Explicar: "Todo indicador debe pasar validación definida en config/data_contracts.yaml"
  - [ ] Incluir: cuándo se ejecuta, cómo debuggear fallos
- [ ] Revisar commit message: "AGENT_4: Documentar enforcement de data contracts"

#### Verificación
```bash
# Verificar que documentación menciona data_contracts.yaml
grep -r "data_contracts" docs/  # DEBE encontrar
grep -r "data_contracts" .ai/PROJECT_RULES.md  # DEBE encontrar
```

---

### TAREA 2.4: Agregar Versionado a Documentos

**Desincronización:** H10 — Falta de Versionado  
**Owner:** Technical Writer  
**Tiempo Estimado:** 30 minutos  
**Complejidad:** 🟢 TRIVIAL

#### Checklist
- [ ] Crear template en [docs/DOCUMENT_TEMPLATE.md](docs/DOCUMENT_TEMPLATE.md):
  ```markdown
  # [Título del Documento]
  
  > **Última actualización:** 2026-05-09  
  > **Status:** ✅ VIGENTE | ⚠️ PARCIAL | 🔴 OBSOLETO  
  > **Owner:** [Nombre]
  
  (resto del documento)
  ```
- [ ] Actualizar TODOS los docs en [docs/core/](docs/core/) con fecha:
  - [ ] [docs/core/01_Arquitectura.md](docs/core/01_Arquitectura.md): cambiar fecha (22 abr → 9 may)
  - [ ] [docs/core/02_Logica_Indicadores.md](docs/core/02_Logica_Indicadores.md): actualizar
  - [ ] [docs/core/03_Modelo_Datos.md](docs/core/03_Modelo_Datos.md): actualizar
  - [ ] [docs/core/04_Dashboard.md](docs/core/04_Dashboard.md): actualizar
  - [ ] [docs/core/05_Operativo.md](docs/core/05_Operativo.md): actualizar
  - [ ] [docs/core/06_Testing_Calidad.md](docs/core/06_Testing_Calidad.md): actualizar
  - [ ] [docs/core/07_Decisiones.md](docs/core/07_Decisiones.md): actualizar
- [ ] Revisar commit message: "AGENT_4: Agregar versionado y ownership a documentación"

#### Verificación
```bash
# Verificar que docs tienen fecha de actualización
grep -r "Última actualización" docs/core/  # DEBE encontrar en todos
grep "2026-05-09" docs/core/*.md  # Debe encontrar en línea 3-5 de cada archivo
```

---

## 🟢 PHASE 3: LIMPIEZA (Semana 3-4 — 23-27 mayo 2026)

### TAREA 3.1: Revisar docs/archive/

**Desincronización:** H13 — Documentación Histórica  
**Owner:** Architect  
**Tiempo Estimado:** 1 hora  
**Complejidad:** 🟢 TRIVIAL

#### Checklist
- [ ] Revisar cada archivo en [docs/archive/](docs/archive/):
  - [ ] 02-MODELO-DATOS/DATA-CONTRACTS.md — ¿Obsoleto vs config/data_contracts.yaml?
  - [ ] 05-FASE2/ — ¿Necesario para auditoría histórica?
  - [ ] FUENTES_DATOS_PROYECTO.md — ¿Reemplazado por docs/core/03_Modelo_Datos.md?
  - [ ] INDEX.md — ¿Reemplazado por docs/README.md?
  - [ ] FUENTES_POR_PAGINA.md — ¿Actualizado?
- [ ] Decisión por archivo: MANTENER | ELIMINAR | MOVER
- [ ] Documentar decisión en [docs/archive/README.md](docs/archive/README.md) (crear si no existe)
- [ ] Revisar commit message: "AGENT_4: Limpiar docs/archive/ — decisiones documentadas"

#### Verificación
```bash
ls -la docs/archive/
# Cada subdirectorio debe tener README.md explicando propósito
```

---

### TAREA 3.2: Consolidar Configuración Streamlit

**Desincronización:** H12 — Config Inconsistencia  
**Owner:** DevOps  
**Tiempo Estimado:** 30 minutos  
**Complejidad:** 🟢 TRIVIAL

#### Checklist
- [ ] Revisar [.streamlit/](/.streamlit/):
  - [ ] config.toml → OK
  - [ ] secrets.toml.template → Crear si no existe
  - [ ] secrets_ejemplo.toml → ELIMINAR (renombrar a .toml.template)
- [ ] Crear [.streamlit/README.md](.streamlit/README.md):
  ```markdown
  # .streamlit/ — Configuración de Streamlit
  
  ## Archivos
  - config.toml: Configuración del servidor
  - secrets.toml.template: Plantilla (copiar a secrets.toml local, NUNCA commitear)
  - AUTH_CONFIG.md: Configuración de autenticación OIDC
  - DEPLOY_CHECKLIST.md: Checklist pre-deployment
  
  ## Setup Local
  cp secrets.toml.template secrets.toml
  # Llenar valores en secrets.toml
  streamlit run streamlit_app/app.py
  ```
- [ ] Revisar .gitignore: debe incluir `.streamlit/secrets.toml`
- [ ] Revisar commit message: "AGENT_4: Estandarizar configuración .streamlit/"

---

### TAREA 3.3: Limpiar HTML Legacy

**Desincronización:** H11 — HTML sin Control  
**Owner:** Frontend  
**Tiempo Estimado:** 30 minutos  
**Complejidad:** 🟢 TRIVIAL

#### Checklist
- [ ] Revisar archivos:
  - [ ] [dashboard_diplomatic.html](dashboard_diplomatic.html)
  - [ ] [dashboard_profesional_v2.html](dashboard_profesional_v2.html)
  - [ ] [dashboard_prueba.html](dashboard_prueba.html)
- [ ] Determinar: ¿Se usan en producción?
  - [ ] Si NO → mover a [docs/archive/prototypes/](docs/archive/prototypes/)
  - [ ] Si SÍ → documentar en [docs/core/04_Dashboard.md](docs/core/04_Dashboard.md)
- [ ] Si se mueven, actualizar .gitignore
- [ ] Revisar commit message: "AGENT_4: Archivando HTML legacy"

#### Verificación
```bash
# Verificar que no hay HTML suelto en raíz
ls *.html
# Si existen, deben estar documentados en docs/core/04_Dashboard.md
```

---

## 📊 TRACKING CENTRAL

**Usar esta tabla para monitoreo diario:**

| Tarea | Owner | Status | Compl. % | Bloques | Notas |
|-------|-------|--------|----------|---------|-------|
| 1.1: Actualizar README.md | PM | ⏳ | 0% | - | - |
| 1.2: Refactor categorizar_cumpl() | Backend | ⏳ | 0% | - | - |
| 1.3: Documentar consolidar_api | TechWriter | ⏳ | 0% | - | - |
| 1.4: Auditoría Auth | DevOps | ⏳ | 0% | - | - |
| 2.1: Alinear GOVERNANCE.md | Arch | ⏳ | 0% | 1.x | - |
| 2.2: Documentar consolidation/ | Backend | ⏳ | 0% | 1.x | - |
| 2.3: Data Contracts docs | Backend | ⏳ | 0% | 1.x | - |
| 2.4: Versionado docs | TechWriter | ⏳ | 0% | 1.x | - |
| 3.1: Limpiar archive/ | Arch | ⏳ | 0% | 2.x | - |
| 3.2: Config Streamlit | DevOps | ⏳ | 0% | 2.x | - |
| 3.3: HTML Legacy | Frontend | ⏳ | 0% | 2.x | - |

**Leyenda:** ⏳ No iniciado | 🔄 En progreso | ✅ Completado | ❌ Bloqueado

---

**Documento de Referencia:**  
[AGENT_4_DESINCRONIZACIONES_20260509.md](AGENT_4_DESINCRONIZACIONES_20260509.md)

**Última Actualización:** 9 de mayo de 2026
