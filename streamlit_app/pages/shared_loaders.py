"""
Shared data loading functions for pages modules.

Common functions to load and prepare data from various sources
(consolidados, cierres, Kawak, PDI) used across page modules.
"""
import pandas as pd


def parse_month_value(value) -> int | None:
    """
    Parsea un valor mes desde diferentes formatos.
    
    Soporta:
    - Enteros 1-12
    - Strings numéricos "1"-"12"
    - Nombres de mes en español ("Enero", "Febrero", etc.)
    - Valores inválidos retornan None
    
    Args:
        value: Valor mes a parsear
        
    Returns:
        int | None: Número de mes (1-12) o None si inválido
    """
    MONTH_NAMES = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    
    if pd.isna(value):
        return None
    
    # Try as integer
    try:
        month_int = int(value)
        if 1 <= month_int <= 12:
            return month_int
    except (ValueError, TypeError):
        pass
    
    # Try as month name
    try:
        month_name = str(value).strip().lower()
        return MONTH_NAMES.get(month_name, None)
    except Exception:
        pass
    
    return None


def get_available_years(df: pd.DataFrame, year_col: str = "Anio") -> list[int]:
    """
    Obtiene años únicos disponibles en un DataFrame.
    
    Args:
        df: DataFrame con datos
        year_col: Nombre de la columna de años
        
    Returns:
        list[int]: Lista de años ordenada ascendente
    """
    if year_col not in df.columns:
        return []
    
    years = pd.to_numeric(df[year_col], errors="coerce").dropna().unique().astype(int).tolist()
    return sorted(years)


def get_latest_month_for_year(df: pd.DataFrame, year: int, 
                               year_col: str = "Anio", month_col: str = "Mes") -> int | None:
    """
    Obtiene el mes más reciente para un año específico.
    
    Args:
        df: DataFrame con datos
        year: Año a buscar
        year_col: Nombre de la columna de años
        month_col: Nombre de la columna de meses
        
    Returns:
        int | None: Número de mes (1-12) o None si no hay datos
    """
    if year_col not in df.columns or month_col not in df.columns:
        return None
    
    year_data = df[pd.to_numeric(df[year_col], errors="coerce") == year].copy()
    
    if year_data.empty:
        return None
    
    months = pd.to_numeric(year_data[month_col], errors="coerce").dropna().astype(int)
    
    if months.empty:
        return None
    
    return int(months.max())


def get_available_months_for_year(df: pd.DataFrame, year: int,
                                   year_col: str = "Anio", month_col: str = "Mes") -> list[int]:
    """
    Obtiene meses disponibles para un año específico.
    
    Args:
        df: DataFrame con datos
        year: Año a buscar
        year_col: Nombre de la columna de años
        month_col: Nombre de la columna de meses
        
    Returns:
        list[int]: Lista de meses (1-12) ordenada ascendente
    """
    if year_col not in df.columns or month_col not in df.columns:
        return []
    
    year_data = df[pd.to_numeric(df[year_col], errors="coerce") == year].copy()
    
    if year_data.empty:
        return []
    
    months = pd.to_numeric(year_data[month_col], errors="coerce").dropna().astype(int).unique().tolist()
    
    return sorted(months)


def normalize_columns(df: pd.DataFrame, case: str = "title") -> pd.DataFrame:
    """
    Normaliza nombres de columnas.
    
    Args:
        df: DataFrame original
        case: Caso a normalizar ("title", "upper", "lower", "snake")
        
    Returns:
        pd.DataFrame: DataFrame con columnas normalizadas
    """
    df = df.copy()
    
    if case == "title":
        df.columns = [col.strip().title() for col in df.columns]
    elif case == "upper":
        df.columns = [col.strip().upper() for col in df.columns]
    elif case == "lower":
        df.columns = [col.strip().lower() for col in df.columns]
    elif case == "snake":
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    
    return df
