"""
Custom JSON serialization utilities for numpy/pandas types.

Provides a default handler for json.dumps() that safely converts
numpy arrays, pandas Series, and other non-standard types to
JSON-serializable formats.
"""
from typing import Any


def json_default(o: Any):
    """
    Serializador por defecto para json.dumps que convierte tipos de numpy/pandas.
    
    Maneja conversión automática de:
    - numpy integers/floats → Python int/float
    - numpy arrays → lists
    - pandas Series → lists
    - pandas Timestamp → ISO format string
    - pandas Timedelta → string representation
    - pandas NA/NaN → None
    
    Args:
        o: Objeto a serializar
        
    Returns:
        Representación JSON-serializable del objeto
        
    Raises:
        TypeError: Si el tipo no puede ser serializado
    """
    try:
        import numpy as _np
        import pandas as _pd
    except Exception:
        _np = None
        _pd = None

    # pandas NA / numpy nan
    try:
        if _pd is not None and _pd.isna(o):
            return None
    except Exception:
        pass

    # Numpy types
    if _np is not None:
        if isinstance(o, _np.integer):
            return int(o)
        if isinstance(o, _np.floating):
            return float(o)
        if isinstance(o, _np.ndarray):
            return o.tolist()

    # Pandas types
    if _pd is not None:
        if isinstance(o, _pd.Series):
            return o.tolist()
        if isinstance(o, _pd.Timestamp):
            return o.isoformat()
        if isinstance(o, _pd.Timedelta):
            return str(o)

    # Fallback: intentar extraer valor con .item() si existe
    if hasattr(o, "item"):
        try:
            return o.item()
        except Exception:
            pass

    # Si nada funcionó, dejar que json.dumps lance el error
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
