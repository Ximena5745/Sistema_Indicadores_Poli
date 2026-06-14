"""Umbrales y constantes de negocio — portados desde core/config.py."""

from enum import Enum

UMBRAL_PELIGRO = 0.80
UMBRAL_ALERTA = 1.00
UMBRAL_SOBRECUMPLIMIENTO = 1.05
UMBRAL_ALERTA_PA = 0.95
UMBRAL_SOBRECUMPLIMIENTO_PA = 1.00

# Fallback desde settings.toml [business] si no se carga Excel
IDS_PLAN_ANUAL_DEFAULT = frozenset(
    {"373", "390", "414", "415", "416", "417", "418", "420", "469", "470", "471"}
)
IDS_TOPE_100 = frozenset({"208", "218"})

RANGO_CUMPLIMIENTO_MIN = 0.0
RANGO_CUMPLIMIENTO_MAX = 1.3

COLOR_CATEGORIA = {
    "Peligro": "#D32F2F",
    "Alerta": "#FBAF17",
    "Cumplimiento": "#43A047",
    "Sobrecumplimiento": "#6699FF",
    "Sin dato": "#BDBDBD",
}


class CategoriaCumplimiento(str, Enum):
    PELIGRO = "Peligro"
    ALERTA = "Alerta"
    CUMPLIMIENTO = "Cumplimiento"
    SOBRECUMPLIMIENTO = "Sobrecumplimiento"
    SIN_DATO = "Sin dato"
