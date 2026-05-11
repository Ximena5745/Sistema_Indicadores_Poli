"""
Configuration for pdi_acreditacion page.
"""

# Filter definitions
FILTER_DEFINITIONS = [
    {
        "key": "estado",
        "label": "Estado",
        "type": "selectbox",
        "options": ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"],
        "include_all": True,
    },
    {
        "key": "macro",
        "label": "Macrolínea",
        "type": "selectbox",
        "options": ["Docencia", "Investigación", "Extensión", "Gobierno"],
        "include_all": True,
    },
    {
        "key": "horizonte",
        "label": "Horizonte",
        "type": "selectbox",
        "options": ["2026-1", "2026-2", "2027-1"],
        "default": "2026-1",
        "include_all": False,
    },
]

# Columns to display in matrix
MATRIX_COLUMNS = [
    "Id",
    "Indicador",
    "Linea",
    "Objetivo",
    "cumplimiento_pct",
    "Meta",
    "Ejecucion",
    "Estado",
    "Meta_Signo",
    "Meta s",
    "MetaS",
    "Ejecucion_Signo",
    "Ejecución s",
    "Ejecucion s",
    "EjecS",
    "Decimales",
    "Decimales_Meta",
    "Decimales_Ejecucion",
    "DecimalesEje",
    "DecMeta",
    "DecEjec",
]

# CNA data source path  
CNA_SHEET = "Worksheet"
