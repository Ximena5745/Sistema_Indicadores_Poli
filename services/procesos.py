"""
services/procesos.py — Gestión centralizada de mapeos de procesos.

Carga mapeos de config/mapeos_procesos.yaml → precarga → caché Streamlit →
disponible para toda la app sin redeploy para cambios de mapeos.
"""

import unicodedata
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
import yaml

from core.config import DATA_RAW

# Rutas
_CONFIG_ROOT = Path(__file__).resolve().parent.parent / "config"
_MAPEOS_YAML = _CONFIG_ROOT / "mapeos_procesos.yaml"


def _normalizar_texto(texto: str) -> str:
    """Normaliza para comparación: lowercase, remove tildes."""
    if not isinstance(texto, str):
        texto = str(texto or "")
    nfd = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


@st.cache_resource(show_spinner="Cargando mapeos de procesos...")
def cargar_mapeos_procesos() -> dict[str, str]:
    """Carga mapeos subproceso → proceso desde YAML.

    Estructura YAML esperada:
        PROCESO_PADRE_1:
          - "Subproceso A"
          - "Subproceso B"
        PROCESO_PADRE_2:
          - "Subproceso C"

    Retorna:
        {subproceso_normalizado: proceso_padre}
        Ej: {"gestion docente": "DOCENCIA", ...}
    """
    if not _MAPEOS_YAML.exists():
        st.warning(f"Archivo de mapeos no encontrado: {_MAPEOS_YAML}")
        return {}

    try:
        with open(_MAPEOS_YAML, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        st.error(f"Error cargando mapeos_procesos.yaml: {e}")
        return {}

    # Invertir estructura: (proceso) -> [subprocs] a (subproc_norm) -> proceso
    mapeo_inverso = {}
    for proceso, subprocesos in config.items():
        if not isinstance(subprocesos, list):
            continue
        for sub in subprocesos:
            if sub and isinstance(sub, str):
                clave = _normalizar_texto(sub)
                mapeo_inverso[clave] = str(proceso).strip()

    return mapeo_inverso


@st.cache_data(ttl=600, show_spinner=False)
def obtener_proceso_padre(subproceso: str) -> Optional[str]:
    """Busca proceso padre para un subproceso.

    Args:
        subproceso: nombre del subproceso tal como viene en data

    Returns:
        Nombre del proceso padre (en MAYÚSCULAS) o None si no encontrado

    Ejemplo:
        obtener_proceso_padre("Gestion Docente") → "DOCENCIA"
    """
    if not subproceso or pd.isna(subproceso):
        return None

    mapeos = cargar_mapeos_procesos()
    clave = _normalizar_texto(str(subproceso))
    return mapeos.get(clave)


def validar_procesos_en_dataset(df: pd.DataFrame) -> dict[str, list[str]]:
    """Valida que todos los subprocesos en df tengan mapeo.

    Args:
        df: DataFrame con columna "Subproceso"

    Returns:
        {
            "con_mapeo": count,
            "sin_mapeo": [lista de subprocesos sin mapeo],
            "total": count
        }
    """
    if "Subproceso" not in df.columns:
        return {"con_mapeo": 0, "sin_mapeo": [], "total": 0}

    mapeos = cargar_mapeos_procesos()
    sin_mapeo = set()
    con_mapeo = 0

    for sub in df["Subproceso"].dropna().unique():
        sub = str(sub).strip()
        if not sub:
            continue

        if _normalizar_texto(sub) in mapeos:
            con_mapeo += 1
        else:
            sin_mapeo.add(sub)

    return {
        "con_mapeo": con_mapeo,
        "sin_mapeo": sorted(list(sin_mapeo)),
        "total": con_mapeo + len(sin_mapeo),
    }


def enriquecer_dataset_con_procesos(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columna ProcesoPadre basada en Subproceso.

    Args:
        df: DataFrame con columna "Subproceso"

    Returns:
        df con nueva columna "Proceso_Padre" (sin modificar original)
    """
    if "Subproceso" not in df.columns:
        return df

    df_out = df.copy()
    df_out["Proceso_Padre"] = df_out["Subproceso"].apply(obtener_proceso_padre)
    return df_out


def validar_integridad_mapeos() -> dict:
    """Valida mapeos contra Subproceso-Proceso-Area.xlsx si existe.

    Returns:
        {
            "archivo_encontrado": bool,
            "mapeos_encontrados_en_yaml": int,
            "nuevos_en_excel": [lista],
            "discrepancias": [lista de (subproceso, proceso_yaml, proceso_excel)]
        }
    """
    resultado = {
        "archivo_encontrado": False,
        "mapeos_encontrados_en_yaml": 0,
        "nuevos_en_excel": [],
        "discrepancias": [],
    }

    mapeos_yaml = cargar_mapeos_procesos()
    resultado["mapeos_encontrados_en_yaml"] = len(mapeos_yaml)

    path_excel = DATA_RAW / "Subproceso-Proceso-Area.xlsx"
    if not path_excel.exists():
        return resultado

    resultado["archivo_encontrado"] = True

    try:
        df = pd.read_excel(str(path_excel), engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]

        col_sub = next((c for c in df.columns if "ubproceso" in c.lower()), None)
        col_pro = next(
            (c for c in df.columns if "roceso" in c.lower() and "ubproceso" not in c.lower()), None
        )

        if not col_sub or not col_pro:
            return resultado

        for _, row in df.iterrows():
            if pd.isna(row[col_sub]) or pd.isna(row[col_pro]):
                continue

            sub = str(row[col_sub]).strip()
            pro = str(row[col_pro]).strip()

            if not sub or pro.lower() in ("no aplica", ""):
                continue

            clave = _normalizar_texto(sub)

            # Registrar nuevos encontrados en Excel
            if clave not in mapeos_yaml:
                resultado["nuevos_en_excel"].append((sub, pro))

            # Registrar discrepancias
            elif mapeos_yaml[clave] != pro:
                resultado["discrepancias"].append((sub, mapeos_yaml[clave], pro))

    except Exception as e:
        resultado["error"] = str(e)

    return resultado
