"""
scripts/etl/signos.py
Extracción del mapa de signos (Meta_Signo, Ejecucion_Signo, Decimales)
desde los DataFrames históricos existentes.
"""
from __future__ import annotations

import logging
from typing import Dict

import pandas as pd

from .no_aplica import SIGNO_NA
from .normalizacion import _id_str

logger = logging.getLogger(__name__)


def obtener_signos(
    df_hist: pd.DataFrame,
    df_sem: pd.DataFrame,
    df_cierres: pd.DataFrame,
    formato_valores_map: Dict[str, str] | None = None,
) -> Dict[str, Dict]:
    """
    Construye {id_str: {meta_signo, ejec_signo, dec_meta, dec_ejec}}
    leyendo los tres DataFrames históricos en orden cronológico.

    Regla base (histórico): el último signo real encontrado prevalece;
           'No Aplica' solo sobreescribe si no hay signo real previo.

    Si se pasa formato_valores_map ({id_str: 'ENT'|'%'|'$'|...}, desde la
    columna 'Formato_Valores' del catálogo), éste tiene PRIORIDAD sobre el
    histórico: el histórico solo perpetúa lo que ya había en el consolidado
    (p.ej. "%" heredado de cuando un indicador se calculaba distinto), sin
    detectar cuándo queda desincronizado del formato real del indicador
    (hallado en 274 y 200+ ids más, feedback 2026-07-26). Sub-indicadores
    con Id decimal (274.1) que no están en el catálogo heredan el formato
    de su padre (274). 'No Aplica' sigue aplicándose por fila en tiempo de
    escritura (escritura.escribir_filas), no aquí — no se ve afectado.
    """
    signos: Dict[str, Dict] = {}
    col_ejec_candidates = [
        "Ejecucion_Signo", "Ejecución Signo", "Ejecucion Signo",
        "Ejecución s", "Ejecucion s",
    ]
    col_ms_candidates = ["Meta_Signo", "Meta Signo", "Meta s"]

    for df in [df_hist, df_sem, df_cierres]:
        col_ms = next((c for c in col_ms_candidates if c in df.columns), None)
        col_es = next((c for c in col_ejec_candidates if c in df.columns), None)
        col_dm = "Decimales_Meta"      if "Decimales_Meta"      in df.columns else None
        col_de = "Decimales_Ejecucion" if "Decimales_Ejecucion" in df.columns else None

        for _, row in df.sort_values("Fecha").iterrows():
            id_s = str(row["Id"])
            ejec_signo_raw = row.get(col_es, "%") if col_es else "%"

            # Normalizar variantes de "No Aplica"
            if str(ejec_signo_raw).strip().lower() in ("no aplica", "n/a"):
                ejec_signo_raw = SIGNO_NA

            # No sobreescribir signo real con No Aplica
            if (
                ejec_signo_raw == SIGNO_NA
                and id_s in signos
                and signos[id_s]["ejec_signo"] != SIGNO_NA
            ):
                continue

            signos[id_s] = {
                "meta_signo": row.get(col_ms, "%") if col_ms else "%",
                "ejec_signo": ejec_signo_raw,
                "dec_meta":   row.get(col_dm, 0) if col_dm else 0,
                "dec_ejec":   row.get(col_de, 0) if col_de else 0,
            }

    if formato_valores_map:
        for id_s, entry in signos.items():
            id_norm = _id_str(id_s)
            fv = formato_valores_map.get(id_norm)
            if not fv:
                padre = id_norm.split(".")[0]
                if padre != id_norm:
                    fv = formato_valores_map.get(padre)
            if fv:
                entry["meta_signo"] = fv
                entry["ejec_signo"] = fv

        # Indicadores en catálogo sin fila histórica previa (nunca
        # escritos aún): que arranquen con el formato correcto en vez
        # del "%" por defecto de escribir_filas.
        for id_s, fv in formato_valores_map.items():
            if id_s not in signos and fv:
                signos[id_s] = {
                    "meta_signo": fv, "ejec_signo": fv,
                    "dec_meta": 0, "dec_ejec": 0,
                }

    return signos
