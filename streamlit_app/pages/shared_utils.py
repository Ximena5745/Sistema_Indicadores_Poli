"""
Shared utility functions for pages modules.

Common normalization, categorization, and text processing utilities
used across multiple page modules (resumen_general.py, resumen_por_proceso.py).
"""
import unicodedata
import pandas as pd


# ─── Text Normalization ───────────────────────────────────────────────────────

def normalize_key(value: str) -> str:
    """
    Normaliza una clave de texto para comparación case-insensitive y sin acentos.
    
    Convierte a mayúsculas, elimina diacríticos (acentos, tildes) y caracteres combinados.
    Útil para matchear valores con variaciones de formato.
    
    Args:
        value: Texto a normalizar
        
    Returns:
        str: Texto normalizado en mayúsculas sin acentos
    """
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


# ─── DataFrame Utilities ───────────────────────────────────────────────────────

def ensure_column_exists(df: pd.DataFrame, col_name: str, default_value: str = "Sin dato") -> pd.DataFrame:
    """
    Asegura que una columna existe en el DataFrame.
    
    Si la columna no existe, la añade con un valor por defecto.
    
    Args:
        df: DataFrame original
        col_name: Nombre de la columna a verificar/crear
        default_value: Valor a usar si se crea la columna
        
    Returns:
        pd.DataFrame: DataFrame con la columna garantizada
    """
    if col_name not in df.columns:
        df = df.copy()
        df[col_name] = default_value
    return df


def dedup_by_columns(df: pd.DataFrame, subset: list[str] = None, keep: str = "first") -> pd.DataFrame:
    """
    Elimina duplicados en un DataFrame manteniendo el orden.
    
    Args:
        df: DataFrame con posibles duplicados
        subset: Columnas a considerar para deduplicación. Si es None, usa todas.
        keep: Qué duplicado mantener ('first', 'last', False para eliminar todos)
        
    Returns:
        pd.DataFrame: DataFrame sin duplicados
    """
    if subset and not all(col in df.columns for col in subset):
        subset = [col for col in subset if col in df.columns]
    
    return df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)


# ─── Nivel de Cumplimiento Categorization ─────────────────────────────────────

NIVEL_COLORS = {
    "sobrecumplimiento": "#6699FF",
    "cumplimiento": "#2E7D32",
    "alerta": "#F9A825",
    "peligro": "#C62828",
    "sin dato": "#6E7781",
}

NIVEL_THRESHOLDS = {
    "sobrecumplimiento": 120,
    "cumplimiento": 80,
    "alerta": 60,
    "peligro": 0,
    "sin dato": None,
}


def categorize_compliance_level(value: float) -> str:
    """
    Categoriza un valor de cumplimiento en niveles.
    
    Umbrales:
    - ≥120%: Sobrecumplimiento (#6699FF)
    - 80-120%: Cumplimiento (#2E7D32)
    - 60-80%: Alerta (#F9A825)
    - <60%: Peligro (#C62828)
    - NaN/None: Sin dato (#6E7781)
    
    Args:
        value: Porcentaje de cumplimiento (0-100+)
        
    Returns:
        str: Nivel categorizado ('sobrecumplimiento', 'cumplimiento', 'alerta', 'peligro', 'sin dato')
    """
    if pd.isna(value):
        return "sin dato"
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "sin dato"
    
    if value >= 120:
        return "sobrecumplimiento"
    elif value >= 80:
        return "cumplimiento"
    elif value >= 60:
        return "alerta"
    else:
        return "peligro"


def get_color_for_level(level: str) -> str:
    """
    Retorna el color hexadecimal para un nivel de cumplimiento.
    
    Args:
        level: Nivel de cumplimiento ('sobrecumplimiento', 'cumplimiento', 'alerta', 'peligro', 'sin dato')
        
    Returns:
        str: Color hexadecimal (ej: '#6699FF')
    """
    return NIVEL_COLORS.get(level, NIVEL_COLORS["sin dato"])


def ensure_nivel_cumplimiento_column(df: pd.DataFrame, pct_col: str = None) -> pd.DataFrame:
    """
    Asegura que existe una columna "Nivel de cumplimiento" con categorías válidas.
    
    Si la columna no existe, la crea calculando a partir de porcentaje (pct_col).
    Si no hay porcentaje disponible, llena con "Sin dato".
    
    Args:
        df: DataFrame original
        pct_col: Nombre de la columna con porcentajes. Por defecto busca "Cumplimiento_pct" o "cumplimiento_pct"
        
    Returns:
        pd.DataFrame: DataFrame con columna "Nivel de cumplimiento"
    """
    if "Nivel de cumplimiento" in df.columns:
        return df
    
    df = df.copy()
    
    # Detectar columna de porcentaje si no se proporciona
    if pct_col is None:
        if "Cumplimiento_pct" in df.columns:
            pct_col = "Cumplimiento_pct"
        elif "cumplimiento_pct" in df.columns:
            pct_col = "cumplimiento_pct"
    
    if pct_col and pct_col in df.columns:
        df["Nivel de cumplimiento"] = df[pct_col].apply(categorize_compliance_level)
    else:
        df["Nivel de cumplimiento"] = "Sin dato"
    
    return df
