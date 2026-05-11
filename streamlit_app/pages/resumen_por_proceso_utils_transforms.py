"""Data transformation utility functions for resumen_por_proceso page."""

import unicodedata
import pandas as pd
import numpy as np

from streamlit_app.pages.resumen_por_proceso_config import (
    THRESHOLD_SOBRECUMPLIMIENTO, THRESHOLD_CUMPLIMIENTO, THRESHOLD_ALERTA,
    COMPLIANCE_LEVELS, MESES_OPCIONES, MES_MAP
)
from core.proceso_types import TIPOS_PROCESO, get_tipo_color
from core.semantica import normalizar_valor_a_porcentaje


def _norm_key(value: str) -> str:
    """Normalize string key (uppercase, NFKD, remove diacritics)."""
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _norm_text(value) -> str:
    """Text normalization for display."""
    return _norm_key(value)


def _to_float(value) -> float | None:
    """Convert value to float, handling percentage strings."""
    if pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    text = str(value).strip().replace("%", "").strip()
    try:
        return float(text)
    except Exception:
        return None


def _mes_to_num(value, periodicidad: str | None = None) -> float | None:
    """Convert month string/number to month number (1-12)."""
    if pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except Exception:
            return None
    
    text = str(value).strip().upper()
    num = MES_MAP.get(text)
    
    if num is not None:
        return num
    
    # Handle semestral logic
    if periodicidad and "SEMESTRAL" in str(periodicidad).upper():
        if num in [6, 12]:
            return num
    
    return None


def _categoria_por_pct(pct: float) -> str:
    """Categorize compliance percentage."""
    if pd.isna(pct):
        return "Sin dato"
    
    try:
        pct = float(pct)
    except Exception:
        return "Sin dato"
    
    if pct >= THRESHOLD_SOBRECUMPLIMIENTO:
        return "Sobrecumplimiento"
    elif pct >= THRESHOLD_CUMPLIMIENTO:
        return "Cumplimiento"
    elif pct >= THRESHOLD_ALERTA:
        return "Alerta"
    else:
        return "Peligro"


def _ensure_nivel_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure 'Nivel de cumplimiento' column exists."""
    if "Nivel de cumplimiento" in df.columns:
        return df
    
    df = df.copy()
    
    pct_col = None
    if "Cumplimiento_pct" in df.columns:
        pct_col = "Cumplimiento_pct"
    elif "cumplimiento_pct" in df.columns:
        pct_col = "cumplimiento_pct"
    
    if pct_col is None:
        df["Nivel de cumplimiento"] = "Sin dato"
    else:
        df["Nivel de cumplimiento"] = df[pct_col].apply(_categoria_por_pct)
    
    return df


def _process_counts_cmi(df: pd.DataFrame, process_col: str) -> pd.DataFrame:
    """Build compliance level crosstab by process."""
    if df.empty or process_col not in df.columns:
        return pd.DataFrame(columns=[process_col] + COMPLIANCE_LEVELS)
    
    df = _ensure_nivel_cumplimiento(df)
    
    crosstab = pd.crosstab(
        df[process_col], 
        df["Nivel de cumplimiento"],
        margins=False
    )
    
    for col in COMPLIANCE_LEVELS:
        if col not in crosstab.columns:
            crosstab[col] = 0
    
    return crosstab[COMPLIANCE_LEVELS].reset_index()


def _ensure_tipo_proceso_cmi(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure tipo_proceso column exists and is valid."""
    if "tipo_proceso" in df.columns and not df["tipo_proceso"].isna().all():
        return df
    
    df = df.copy()
    
    # Try to infer from Tipo column
    if "Tipo" in df.columns:
        df["tipo_proceso"] = df["Tipo"]
    elif "Tipo_proceso" in df.columns:
        df["tipo_proceso"] = df["Tipo_proceso"]
    else:
        df["tipo_proceso"] = None
    
    # Normalize if exists
    if "tipo_proceso" in df.columns:
        df["tipo_proceso"] = df["tipo_proceso"].apply(
            lambda x: _canonical_tipo_proceso(x)
        )
    
    return df


def _canonical_tipo_proceso(value) -> str | None:
    """Normalize tipo_proceso to official TIPOS_PROCESO value."""
    if pd.isna(value):
        return None
    
    value_norm = _norm_key(str(value))
    
    for tipo in TIPOS_PROCESO:
        if _norm_key(tipo) == value_norm:
            return tipo
    
    return None


def _available_months_with_data(df: pd.DataFrame) -> list[int]:
    """Get list of months (1-12) with non-null Periodo data."""
    months = []
    
    for i in range(1, 13):
        col = f"Periodo {i}"
        if col in df.columns:
            if not df[col].isna().all():
                months.append(i)
    
    return sorted(months)


def _default_month_num(df: pd.DataFrame) -> int:
    """Get default month: latest available or 12."""
    months = _available_months_with_data(df)
    return max(months) if months else 12


def _cumpl_delta(actual, previo) -> tuple[str, str]:
    """Calculate compliance delta vs previous period."""
    actual_f = _to_float(actual)
    previo_f = _to_float(previo)
    
    if actual_f is None or previo_f is None:
        return "—", "#6E7781"
    
    delta = actual_f - previo_f
    color = "#2E7D32" if delta >= 0 else "#C62828"
    
    return f"{delta:+.1f}%", color


def _cumpl_icon(pct: float) -> str:
    """Get emoji icon for compliance percentage."""
    if pd.isna(pct):
        return "⚪"
    
    pct = float(pct)
    if pct >= THRESHOLD_SOBRECUMPLIMIENTO:
        return "🔵"
    elif pct >= THRESHOLD_CUMPLIMIENTO:
        return "🟢"
    elif pct >= THRESHOLD_ALERTA:
        return "🟡"
    else:
        return "🔴"


def _cumpl_label(pct: float) -> str:
    """Format compliance label with icon."""
    icon = _cumpl_icon(pct)
    if pd.isna(pct):
        return "⚪ —"
    return f"{icon} {float(pct):.1f}%"


def _status_color_for_pct(pct: float) -> str:
    """Get color for compliance percentage."""
    categoria = _categoria_por_pct(pct)
    
    color_map = {
        "Sobrecumplimiento": "#6699FF",
        "Cumplimiento": "#2E7D32",
        "Alerta": "#F9A825",
        "Peligro": "#C62828",
        "Sin dato": "#6E7781",
    }
    
    return color_map.get(categoria, "#6E7781")


def _compute_indicador_summary(df: pd.DataFrame, pct_col: str = "cumplimiento_pct") -> dict:
    """Compute summary metrics for indicators."""
    if df.empty:
        return {"total": 0, "promedio": 0, "sobrecumplimiento": 0, 
                "cumplimiento": 0, "alerta": 0, "peligro": 0}
    
    df = _ensure_nivel_cumplimiento(df)
    nivel_col = "Nivel de cumplimiento"
    
    total = len(df)
    promedio = df[pct_col].mean() if pct_col in df.columns else 0
    
    return {
        "total": total,
        "promedio": float(promedio),
        "sobrecumplimiento": int((df[nivel_col] == "Sobrecumplimiento").sum()),
        "cumplimiento": int((df[nivel_col] == "Cumplimiento").sum()),
        "alerta": int((df[nivel_col] == "Alerta").sum()),
        "peligro": int((df[nivel_col] == "Peligro").sum()),
    }


def _build_variation_tables(df: pd.DataFrame, ejec_col: str = "Ejecucion") -> tuple:
    """Build top 8 improvements and declines."""
    if df.empty or ejec_col not in df.columns:
        return pd.DataFrame(), pd.DataFrame()
    
    # Calculate variations (simplified for now)
    improvements = df.nlargest(8, ejec_col)
    declines = df.nsmallest(8, ejec_col)
    
    return improvements, declines
