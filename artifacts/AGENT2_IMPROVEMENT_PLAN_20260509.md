# PLAN DE MEJORA — IMPLEMENTACIÓN EJECUTABLE
## Sistema de Indicadores Institucionales (SGIND)

**Generado:** 9 de mayo de 2026  
**Objetivo:** Transformar pipeline ETL de "funcional" a "resiliente + auditable"  
**Duración estimada:** 3-4 semanas (48 horas de desarrollo)

---

## FASE 1: VALIDACIÓN INMEDIATA (Semana 1 — 8 horas)

### 1.1 Quick Win #1: Fija Versiones en requirements.txt
**Duración:** 15 minutos  
**Criticidad:** 🟠 Alta (reproducibilidad)  
**Archivos:** [requirements.txt](requirements.txt)

**Cambio actual:**
```txt
streamlit>=1.36.0
plotly>=5.22.0
pandas>=2.2.2
openpyxl>=3.1.4
xlrd>=2.0.1
numpy>=1.24.0
pyyaml>=6.0
pydantic
```

**Cambio propuesto:**
```txt
streamlit==1.36.0
plotly==5.22.0
pandas==2.2.2
openpyxl==3.1.4
xlrd==2.0.1
numpy==1.24.0
pyyaml==6.0
pydantic==2.5.0
kaleido==0.2.1
Pillow==10.0.0
python-dotenv==1.0.1
sqlalchemy==2.0.23
anthropic==0.40.0
streamlit-extras==0.1.0
streamlit-option-menu==0.3.12
reportlab==4.0.9
pypdf==4.2.0
psycopg2-binary==2.9.9
xlsxwriter==3.2.0
tomli==2.0.1
tenacity==8.2.3
```

**Comando:**
```bash
# Generar versiones exactas de entorno actual
pip freeze > requirements.txt
# O usar pip-tools
pip-compile requirements.in
```

---

### 1.2 Quick Win #2: Logueo de Omisiones en Pipeline
**Duración:** 30 minutos  
**Criticidad:** 🟠 Alta (auditoría)  
**Archivos:** [scripts/etl/builders.py](scripts/etl/builders.py), [scripts/etl/fuentes.py](scripts/etl/fuentes.py)

**Cambio en [scripts/etl/builders.py] — línea 25:**

```python
def construir_registros_historico(
    df_fuente: pd.DataFrame,
    llaves_existentes: Set[str],
    hist_escalas: Dict,
    config_patrones: Optional[Dict] = None,
    mapa_procesos: Optional[Dict] = None,
    kawak_validos: Optional[Set[Tuple[str, int]]] = None,
    extraccion_map: Optional[Dict] = None,
    api_kawak_lookup: Optional[Dict] = None,
    variables_campo_map: Optional[Dict] = None,
    tipo_indicador_map: Optional[Dict] = None,
) -> Tuple[List[Dict], int, int]:
    """Genera registros nuevos para Consolidado Histórico."""
    registros = []
    skipped   = 0
    conteo_na = 0
    
    # NUEVO: Contar razones de skip
    skip_razones = {"sin_llave": 0, "kawak_invalido": 0, "extraccion_fallida": 0, "periodo_invalido": 0}
    
    df = df_fuente[~df_fuente["LLAVE"].isin(llaves_existentes)].dropna(subset=["LLAVE"])

    for row in df.itertuples(index=False):
        if kawak_validos is not None:
            id_s = _id_str(getattr(row, "Id", None) or getattr(row, "ID", ""))
            fecha_raw = getattr(row, "fecha", None)
            try:
                año = pd.to_datetime(fecha_raw).year
            except Exception:
                año = None
            if año is not None and (id_s, año) not in kawak_validos:
                skipped += 1
                skip_razones["kawak_invalido"] += 1  # NUEVO
                continue

        meta, ejec, fuente, es_na = _extraer_registro(
            row, hist_escalas,
            config_patrones=config_patrones,
            extraccion_map=extraccion_map,
            api_kawak_lookup=api_kawak_lookup,
            variables_campo_map=variables_campo_map,
            tipo_indicador_map=tipo_indicador_map,
        )

        if fuente in ("skip", "sin_resultado"):
            skipped += 1
            skip_razones["extraccion_fallida"] += 1  # NUEVO
            continue

        if es_na:
            try:
                fecha_ts = pd.to_datetime(getattr(row, "fecha", None))
            except Exception:
                fecha_ts = None
            periodicidad = str(getattr(row, "Periodicidad", ""))
            if periodicidad and fecha_ts is not None:
                if not _fecha_es_periodo_valido(fecha_ts, periodicidad):
                    skipped += 1
                    skip_razones["periodo_invalido"] += 1  # NUEVO
                    continue
        
        # ... resto del código ...
    
    # NUEVO: Loguear resumen
    logger.info(f"  [Consolidado Historico] {len(registros)} registros nuevos")
    if skipped > 0:
        logger.warning(f"  [Consolidado Historico] {skipped} registros omitidos:")
        for razon, count in skip_razones.items():
            if count > 0:
                logger.warning(f"    - {razon}: {count}")
    
    return registros, skipped, conteo_na
```

---

### 1.3 Quick Win #3: Validación Gate en Entrada (LAYER 1)
**Duración:** 2 horas  
**Criticidad:** 🔴 Crítica (bloquea garbage)  
**Archivos:** [scripts/actualizar_consolidado.py](scripts/actualizar_consolidado.py)

**Nuevo código — agregar después de línea 110:**

```python
# ────────────────────────────────────────────────────────────────
# LAYER 1: VALIDACIÓN DE ENTRADA — Gate centralizado
# ────────────────────────────────────────────────────────────────

def _validar_consolidado_api_entrada(df: pd.DataFrame) -> dict:
    """
    GATE DE VALIDACIÓN CRÍTICA
    
    Valida que Consolidado_API_Kawak.xlsx cumple contrato mínimo
    antes de procesarlo. Si falla, bloquea pipeline.
    
    Retorna: {status: "ok"|"error", error_count, warning_count, issues}
    """
    issues = {"errors": [], "warnings": []}
    
    # 1. Columnas requeridas
    COLS_REQUERIDAS = {"ID", "fecha", "resultado"}
    cols_faltantes = COLS_REQUERIDAS - set(df.columns)
    if cols_faltantes:
        issues["errors"].append(f"Columnas faltantes: {cols_faltantes}")
        return {
            "status": "error",
            "error_count": 1,
            "warning_count": 0,
            "issues": issues,
        }
    
    # 2. Nulos en críticas
    nulos_por_col = df[["ID", "fecha"]].isnull().sum()
    if nulos_por_col.any():
        for col, count in nulos_por_col[nulos_por_col > 0].items():
            issues["errors"].append(f"{count} nulos en columna requerida '{col}'")
    
    # 3. Cardinalidad: ID-fecha única
    duplicados = df.groupby(["ID", "fecha"]).size()
    dup_count = (duplicados > 1).sum()
    if dup_count > 0:
        issues["errors"].append(f"{dup_count} combinaciones ID-fecha duplicadas")
    
    # 4. Rango de fechas
    try:
        fechas = pd.to_datetime(df["fecha"], errors="coerce")
        if fechas.isna().any():
            issues["warnings"].append(f"{fechas.isna().sum()} fechas no convertibles")
        
        fecha_min = fechas.min()
        fecha_max = fechas.max()
        if fecha_min < pd.Timestamp("2022-01-01"):
            issues["warnings"].append(f"Fecha mínima anterior a 2022: {fecha_min.date()}")
        if fecha_max > pd.Timestamp("2030-12-31"):
            issues["warnings"].append(f"Fecha máxima posterior a 2030: {fecha_max.date()}")
    except Exception as e:
        issues["errors"].append(f"Error procesando fechas: {e}")
    
    # 5. Cardinalidad total
    min_expected = 1000  # umbral ajustable
    if len(df) < min_expected:
        issues["warnings"].append(f"Dataset muy pequeño ({len(df)} < {min_expected} esperados)")
    
    # Determinar status final
    status = "error" if issues["errors"] else "ok"
    
    return {
        "status": status,
        "error_count": len(issues["errors"]),
        "warning_count": len(issues["warnings"]),
        "issues": issues,
    }


# ────────────────────────────────────────────────────────────────
# En main(), después de línea 111 (después de cargar_fuente_consolidada)
# ────────────────────────────────────────────────────────────────

def main() -> None:
    # ... código existente ...
    
    logger.info("1. Cargando fuente consolidada API/Kawak…")
    df_api = cargar_fuente_consolidada()
    logger.info("   %d registros fuente", len(df_api))

    # ✨ NUEVO: Gate de validación
    logger.info("1.5 Validando contrato de datos…")
    validacion = _validar_consolidado_api_entrada(df_api)
    
    if validacion["status"] == "error":
        logger.error("❌ VALIDACIÓN FALLIDA — Pipeline bloqueado")
        for err in validacion["issues"]["errors"]:
            logger.error(f"   ERROR: {err}")
        sys.exit(1)
    
    if validacion["warning_count"] > 0:
        logger.warning(f"⚠️ {validacion['warning_count']} warnings durante validación:")
        for warn in validacion["issues"]["warnings"]:
            logger.warning(f"   WARN: {warn}")
    
    if validacion["status"] == "ok":
        logger.info(f"✅ Validación OK: {len(df_api)} registros pasaron contrato")
    
    # Continuar con pipeline normal
    logger.info("2. Cargando catálogo…")
    # ... resto del código ...
```

**Prueba:**
```python
# Para testear sin ejecutar pipeline completo:
import pandas as pd
from scripts.etl.fuentes import cargar_fuente_consolidada

df = cargar_fuente_consolidada()
validacion = _validar_consolidado_api_entrada(df)
print(f"Status: {validacion['status']}")
print(f"Errors: {len(validacion['issues']['errors'])}")
print(f"Warnings: {len(validacion['issues']['warnings'])}")
```

---

## FASE 2: REPRODUCIBILIDAD (Semana 2-3 — 14 horas)

### 2.1 Versionado de Consolidados
**Duración:** 4 horas  
**Criticidad:** 🔴 Crítica (recuperabilidad)  
**Archivos:** [scripts/actualizar_consolidado.py](scripts/actualizar_consolidado.py), [scripts/etl/workbook_io.py](scripts/etl/workbook_io.py)

**Código nuevo — agregar en etl/workbook_io.py:**

```python
def crear_versionado_consolidado(output_file: Path, max_versions: int = 5) -> Path:
    """
    Crea backup versionado del consolidado actual.
    Retiene últimos N versiones, elimina las más antiguas.
    
    Args:
        output_file: Ruta del consolidado actual (ej: Resultados Consolidados.xlsx)
        max_versions: Máximo de versiones a retener (default 5)
    
    Returns:
        Ruta del archivo de versión creado
    """
    if not output_file.exists():
        logger.info(f"  Primer ejecutar — no hay versión anterior")
        return None
    
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_dir = output_file.parent / ".versiones"
    version_dir.mkdir(exist_ok=True)
    
    version_path = version_dir / f"{output_file.stem}_v{timestamp}.xlsx"
    shutil.copy(output_file, version_path)
    logger.info(f"  ✅ Backup versionado: {version_path.relative_to(output_file.parent.parent)}")
    
    # Limpiar versiones antiguas
    versiones = sorted(version_dir.glob(f"{output_file.stem}_v*.xlsx"))
    if len(versiones) > max_versions:
        para_eliminar = versiones[:-max_versions]
        for v in para_eliminar:
            v.unlink()
            logger.info(f"  Eliminado version antigua: {v.name}")
    
    return version_path


def restaurar_consolidado_desde_version(output_file: Path, version_timestamp: str = None) -> bool:
    """
    Restaura consolidado desde versión anterior.
    
    Args:
        output_file: Ruta del consolidado actual
        version_timestamp: Timestamp específico (ej "20260509_143015")
                          Si es None, restaura última versión
    
    Returns:
        True si exitoso, False si falló
    """
    version_dir = output_file.parent / ".versiones"
    if not version_dir.exists():
        logger.error("  No hay versiones guardadas")
        return False
    
    versiones = sorted(version_dir.glob(f"{output_file.stem}_v*.xlsx"))
    if not versiones:
        logger.error("  No hay versiones disponibles")
        return False
    
    # Seleccionar versión
    if version_timestamp:
        version_path = version_dir / f"{output_file.stem}_v{version_timestamp}.xlsx"
        if not version_path.exists():
            logger.error(f"  Versión no encontrada: {version_timestamp}")
            return False
    else:
        version_path = versiones[-1]  # última
    
    try:
        shutil.copy(version_path, output_file)
        logger.info(f"  ✅ Restaurado desde: {version_path.name}")
        return True
    except Exception as e:
        logger.error(f"  Error restaurando versión: {e}")
        return False
```

**Integración en actualizar_consolidado.py:**

```python
# Al inicio de main(), después de abrir workbook
logger.info("6. Versionando consolidado anterior…")
from etl.workbook_io import crear_versionado_consolidado
version_path = crear_versionado_consolidado(OUTPUT_FILE, max_versions=5)

# Luego, en try/except para rollback automático
try:
    # ... escribir consolidado ...
    wb.save(str(local_output_file))
    logger.info("✅ Consolidado guardado exitosamente")
    
except Exception as e:
    logger.error(f"❌ Error durante escritura: {e}")
    logger.info("🔄 Intentando rollback…")
    
    if version_path:
        from etl.workbook_io import restaurar_consolidado_desde_version
        if restaurar_consolidado_desde_version(OUTPUT_FILE):
            logger.info("✅ Rollback completado")
    
    raise
```

---

### 2.2 Audit Trail Centralizado
**Duración:** 6 horas  
**Criticidad:** 🔴 Crítica (trazabilidad)  
**Archivos:** Nuevo archivo `scripts/etl/audit.py`, [scripts/actualizar_consolidado.py](scripts/actualizar_consolidado.py)

**Nuevo módulo — crear scripts/etl/audit.py:**

```python
"""
scripts/etl/audit.py
Auditoría centralizada de ejecuciones del ETL.

Registra: usuario, máquina, rama git, timestamp, status, métricas
"""
from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AuditLog:
    """Registro de auditoría de una ejecución ETL"""
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    usuario: str = field(default_factory=lambda: os.getenv("USERNAME", "unknown"))
    maquina: str = field(default_factory=socket.gethostname)
    git_branch: str = ""
    git_commit: str = ""
    accion: str = "consolidate"  # consolidate, validate, etc
    status: str = "pendiente"  # pendiente, success, warning, error
    
    registros_procesados: int = 0
    registros_nuevos: int = 0
    registros_omitidos: int = 0
    registros_duplicados: int = 0
    
    tiempo_total_segundos: float = 0.0
    
    errores: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    
    def to_json(self) -> str:
        """Serializar a JSON"""
        return json.dumps(asdict(self), indent=2, default=str)
    
    def guardar(self, ruta_directorio: Path):
        """Guardar en archivo JSON"""
        ruta_directorio.mkdir(parents=True, exist_ok=True)
        timestamp_file = self.timestamp.replace(":", "").replace("-", "").split(".")[0]
        archivo = ruta_directorio / f"audit_{timestamp_file}.json"
        
        archivo.write_text(self.to_json(), encoding="utf-8")
        logger.info(f"  Auditoría guardada: {archivo.relative_to(ruta_directorio.parent)}")
        return archivo


def obtener_info_git() -> tuple[str, str]:
    """Obtiene rama y commit actual de git"""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        return branch, commit
    except Exception:
        return "unknown", "unknown"


def crear_audit_log(accion: str = "consolidate") -> AuditLog:
    """Crea nuevo registro de auditoría"""
    branch, commit = obtener_info_git()
    
    log = AuditLog(
        accion=accion,
        git_branch=branch,
        git_commit=commit,
    )
    
    logger.info(f"  Usuario: {log.usuario}")
    logger.info(f"  Máquina: {log.maquina}")
    logger.info(f"  Git: {branch} ({commit})")
    
    return log
```

**Integración en actualizar_consolidado.py:**

```python
# Al inicio
from etl.audit import crear_audit_log
import time

def main() -> None:
    logger.info("=" * 65)
    logger.info("  ACTUALIZAR CONSOLIDADO")
    logger.info("=" * 65)
    
    # Crear registro de auditoría
    tiempo_inicio = time.time()
    audit = crear_audit_log(accion="consolidate")
    
    try:
        # ... código normal del pipeline ...
        
        # Al final, antes de return
        audit.status = "success"
        audit.tiempo_total_segundos = time.time() - tiempo_inicio
        
        # Contar métricas (aproximado)
        audit.registros_procesados = len(df_api)
        audit.registros_nuevos = len(registros)  # de builders
        audit.registros_omitidos = skipped
        
        logger.info(f"✅ COMPLETADO en {audit.tiempo_total_segundos:.1f}s")
        
    except Exception as e:
        audit.status = "error"
        audit.errores.append(str(e))
        audit.tiempo_total_segundos = time.time() - tiempo_inicio
        logger.error(f"❌ ERROR: {e}")
        raise
    
    finally:
        # Guardar audit trail
        audit_dir = _ROOT / "artifacts" / "audit"
        audit.guardar(audit_dir)
```

---

### 2.3 Retry Automático
**Duración:** 4 horas  
**Criticidad:** 🟠 Alta (resiliencia)  
**Archivos:** [scripts/etl/fuentes.py](scripts/etl/fuentes.py)

**Instalar dependency:**
```bash
pip install tenacity
```

**Código nuevo — en etl/fuentes.py:**

```python
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
import time

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((IOError, OSError, TimeoutError)),
    before_sleep=lambda retry_state: logger.info(
        f"  Reintentando en {retry_state.next_action.sleep} segundos "
        f"(intento {retry_state.attempt_number}/3)…"
    ),
)
def cargar_fuente_consolidada() -> pd.DataFrame:
    """Lee Consolidado_API_Kawak.xlsx con reintentos automáticos."""
    if not CONSOLIDADO_API_KW.exists():
        logger.error(
            f"No se encontró {CONSOLIDADO_API_KW}.\n"
            "  Ejecutar primero: python scripts/consolidar_api.py"
        )
        return pd.DataFrame()
    
    logger.info(f"  Leyendo {CONSOLIDADO_API_KW.name}…")
    
    df = pd.read_excel(CONSOLIDADO_API_KW)
    df = df.dropna(subset=["fecha"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    
    # ... resto del código ...
    return df
```

---

## FASE 3: NOTIFICACIÓN Y RECUPERACIÓN (Semana 4 — 9 horas)

### 3.1 Notificación de Fallos
**Duración:** 3 horas  
**Criticidad:** 🟠 Alta (visibilidad)  
**Archivos:** [scripts/run_pipeline.py](scripts/run_pipeline.py)

**Código nuevo — crear scripts/notificador.py:**

```python
"""
scripts/notificador.py
Envía notificaciones de fallos del pipeline a stakeholders.
"""
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime


def notificar_fallo(error_msg: str, detalles: dict = None):
    """Envía notificación por email de fallo en pipeline"""
    
    recipients = os.getenv("PIPELINE_NOTIFY_TO", "calidad@institucion.edu").split(",")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL", "pipeline@institucion.edu")
    sender_password = os.getenv("SENDER_PASSWORD", "")
    
    if not sender_password:
        print("⚠️ SMTP_PASSWORD no configurada — notificación no enviada")
        return False
    
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cuerpo = f"""
🚨 ALERTA: Pipeline ETL Fallido

Fecha: {fecha}
Error: {error_msg}

Detalles:
{detalles or {}}

Acción recomendada:
1. Revisar logs en artifacts/pipeline_run_*.log
2. Ejecutar diagnóstico: python scripts/debug_cascada.py
3. Contactar a equipo de datos

---
Sistema: SGIND Pipeline
"""
    
    msg = MIMEText(cuerpo)
    msg["Subject"] = f"🚨 ALERTA: Pipeline ETL Fallido ({fecha})"
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✅ Notificación enviada a: {recipients}")
        return True
    
    except Exception as e:
        print(f"❌ Error enviando notificación: {e}")
        return False


def notificar_exito(resumen: dict = None):
    """Envía notificación de éxito del pipeline"""
    
    recipients = os.getenv("PIPELINE_NOTIFY_TO", "calidad@institucion.edu").split(",")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL", "pipeline@institucion.edu")
    sender_password = os.getenv("SENDER_PASSWORD", "")
    
    if not sender_password:
        return False
    
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cuerpo = f"""
✅ Pipeline ETL Ejecutado Exitosamente

Fecha: {fecha}

Resumen:
{resumen or {}}

Datos consolidados y listos para análisis.

---
Sistema: SGIND Pipeline
"""
    
    msg = MIMEText(cuerpo)
    msg["Subject"] = f"✅ Pipeline ETL Exitoso ({fecha})"
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except:
        return False
```

**Integración en run_pipeline.py:**

```python
from notificador import notificar_fallo, notificar_exito

def main():
    # ... código existente ...
    
    try:
        # Ejecutar pipeline
        resultado = subprocess.run(
            [sys.executable, "scripts/actualizar_consolidado.py"],
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        if resultado.returncode != 0:
            notificar_fallo(
                resultado.stderr,
                {"returncode": resultado.returncode}
            )
            sys.exit(1)
        
        # Si todo OK
        notificar_exito({"registros_procesados": 5234})
        
    except Exception as e:
        notificar_fallo(str(e))
        raise
```

**Configurar variables de entorno (.env):**
```bash
# .env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=pipeline@institucion.edu
SENDER_PASSWORD=<app_password_here>
PIPELINE_NOTIFY_TO=calidad@institucion.edu,datateam@institucion.edu
```

---

## FASE 4: VALIDACIONES ADICIONALES (Semana 4+ — 9 horas)

### 4.1 Gate de Salida — Integridad Referencial
**Duración:** 3 horas  
**Ubicación:** [scripts/etl/escritura.py](scripts/etl/escritura.py)

```python
def validar_integridad_referencial(
    df_hist: pd.DataFrame,
    df_sem: pd.DataFrame,
    df_cierres: pd.DataFrame,
    df_cat: pd.DataFrame,
    logger=None
) -> bool:
    """
    Valida que todos los IDs en consolidados existan en catálogo.
    
    Retorna: True si válido, False si hay inconsistencias.
    """
    if logger is None:
        import logging
        logger = logging.getLogger(__name__)
    
    # Recolectar IDs en consolidado
    ids_consolidado = set()
    for df in [df_hist, df_sem, df_cierres]:
        if "Id" in df.columns:
            ids_consolidado.update(df["Id"].dropna().unique())
    
    # IDs en catálogo
    ids_catalogo = set(df_cat["Id"].dropna().unique())
    
    # Validar
    ids_huerfanos = ids_consolidado - ids_catalogo
    if ids_huerfanos:
        logger.error(
            f"❌ Integridad referencial fallida:\n"
            f"   {len(ids_huerfanos)} IDs huérfanos (en consolidado pero no en catálogo)\n"
            f"   Ejemplos: {list(ids_huerfanos)[:5]}"
        )
        return False
    
    # Advertencia si hay IDs no usados en consolidado
    ids_sin_usar = ids_catalogo - ids_consolidado
    if ids_sin_usar:
        logger.warning(
            f"⚠️ {len(ids_sin_usar)} IDs en catálogo pero no en consolidado"
        )
    
    logger.info("✅ Integridad referencial OK")
    return True
```

---

## MATRIZ DE IMPLEMENTACIÓN RESUMIDA

| # | Tarea | Fase | Duración | Archivos | Prioridad |
|---|-------|------|----------|----------|-----------|
| 1 | Fix requirements.txt | 1 | 15m | requirements.txt | 🔴 P1 |
| 2 | Logueo omisiones | 1 | 30m | etl/builders.py | 🔴 P1 |
| 3 | Gate validación entrada | 1 | 2h | actualizar_consolidado.py | 🔴 P1 |
| 4 | Versionado consolidados | 2 | 4h | etl/workbook_io.py, actualizar_consolidado.py | 🔴 P1 |
| 5 | Audit trail | 2 | 6h | etl/audit.py, actualizar_consolidado.py | 🔴 P1 |
| 6 | Retry automático | 2 | 4h | etl/fuentes.py | 🟠 P2 |
| 7 | Notificación fallos | 3 | 3h | notificador.py, run_pipeline.py | 🟠 P2 |
| 8 | Rollback automático | 3 | 3h | actualizar_consolidado.py | 🟠 P2 |
| 9 | Integridad referencial | 4 | 3h | etl/escritura.py | 🟠 P2 |
| 10 | Patrón regex IDs | 4 | 2h | services/data_validation.py | 🟡 P3 |
| 11 | Validación rango cumpl. | 4 | 2h | etl/validacion_historica.py | 🟡 P3 |

**Total: 48 horas (3-4 semanas)**

---

## COMANDO RÁPIDO PARA COMPILAR TODO

```bash
# Clonar este plan como proyecto
git checkout -b feature/etl-audit-trail

# Implementar en orden: FASE 1 → 2 → 3 → 4
# Testear cada cambio

# Ejecutar tests antes de mergear
pytest tests/test_e2e_pipeline.py -v
pytest tests/test_data_contracts.py -v

# Mergear a main
git merge main
git push origin feature/etl-audit-trail
```

---

**Fin del Plan de Mejora**
