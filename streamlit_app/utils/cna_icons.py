"""
utils/cna_icons.py — Identidad visual de los 12 factores CNA

Fuente: assets/CNA/{1..12}.jpeg — NO son íconos sueltos: cada archivo es la
píldora de color completa ya diseñada (ícono + divisor + nombre del factor,
ver Consolidado.png/Tablero.png). No se recrean con Material Symbols ni con
CSS: se usa la imagen real, embebida como data-URI, ya sea como `<img>}`
completo (grid de factores, vía background del propio botón) o recortada a
la izquierda para mostrar solo el pictograma en usos pequeños (breadcrumb,
headers) — ver `object-position` en `factor_icon_html`.
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

ASSETS_CNA_DIR = Path(__file__).resolve().parents[2] / "assets" / "CNA"


@st.cache_data(ttl=None, show_spinner=False)
def _load_icon_b64(factor_num: int) -> str | None:
    path = ASSETS_CNA_DIR / f"{factor_num}.jpeg"
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def factor_icon_path(factor_num: int) -> Path:
    """Ruta local al ícono — útil para `st.image`."""
    return ASSETS_CNA_DIR / f"{factor_num}.jpeg"


def factor_icon_data_uri(factor_num: int) -> str | None:
    b64 = _load_icon_b64(factor_num)
    return f"data:image/jpeg;base64,{b64}" if b64 else None



# Todas las píldoras comparten la misma plantilla (2064×512 px): el pictograma
# ocupa aproximadamente el 7%-31% del ancho (cápsula redondeada + ícono, antes
# del divisor "|" y el texto). `_ICON_OBJECT_POSITION_X` es el porcentaje de
# object-position que, con object-fit:cover sobre un contenedor cuadrado,
# centra la ventana visible en esa franja (fórmula estándar de
# background-position: offset = (ancho_mostrado - ancho_contenedor) * X%).
# Antes se usaba object-position:left (0%), que dejaba el margen blanco del
# borde izquierdo dentro del recorte y ocultaba el pictograma real.
_ICON_OBJECT_POSITION_X = 8.6


def factor_icon_html(factor_num: int, size: int = 48, rounded: bool = True) -> str:
    """HTML `<img>` recortado al pictograma del factor (o un placeholder si falta).

    La imagen fuente es una píldora ancha (ícono + divisor + texto); se
    recorta con `object-fit: cover` + `object-position` desplazado para
    aislar solo el pictograma en usos pequeños (breadcrumb, headers).
    """
    uri = factor_icon_data_uri(factor_num)
    radius = "50%" if rounded else "8px"
    if uri is None:
        return (
            f'<div style="width:{size}px;height:{size}px;border-radius:{radius};'
            f'background:#EEEEEE;display:inline-flex;align-items:center;justify-content:center;'
            f'font-size:{max(10, size // 3)}px;color:#757575;">{factor_num}</div>'
        )
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:{radius};overflow:hidden;'
        f'display:inline-block;box-shadow:0 1px 4px rgba(0,0,0,0.15);vertical-align:middle;">'
        f'<img src="{uri}" style="width:100%;height:100%;object-fit:cover;'
        f'object-position:{_ICON_OBJECT_POSITION_X}% center;" '
        f'alt="Factor {factor_num}" />'
        f"</div>"
    )
