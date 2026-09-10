"""
utils/cna_icons.py — Íconos numerados de los 12 factores CNA

Fuente: assets/CNA/{1..12}.jpeg. No usa emoji: son las imágenes de
identidad visual provistas para cada factor de acreditación, embebidas como
data-URI para uso inline (breadcrumb, headers, alertas).
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

ASSETS_CNA_DIR = Path(__file__).resolve().parents[2] / "assets" / "CNA"

# Identidad visual por factor — paleta y pictograma tomados de
# assets/CNA/Consolidado.png (el mismo mapa de color se usa en Tablero.png).
# icon = nombre de Material Symbol (sin emoji, por convención del proyecto).
FACTOR_STYLE: dict[int, dict[str, str]] = {
    1: {"icon": "fingerprint", "bg": "#EC0677", "fg": "#FFFFFF"},
    2: {"icon": "visibility", "bg": "#1CA8E0", "fg": "#FFFFFF"},
    3: {"icon": "eco", "bg": "#FBA919", "fg": "#FFFFFF"},
    4: {"icon": "fact_check", "bg": "#17D6E0", "fg": "#0E2F4C"},
    5: {"icon": "account_tree", "bg": "#0E2F4C", "fg": "#FFFFFF"},
    6: {"icon": "query_stats", "bg": "#39B54A", "fg": "#FFFFFF"},
    7: {"icon": "volunteer_activism", "bg": "#7E1E9C", "fg": "#FFFFFF"},
    8: {"icon": "public", "bg": "#1C6B3B", "fg": "#FFFFFF"},
    9: {"icon": "favorite", "bg": "#E31E3C", "fg": "#FFFFFF"},
    10: {"icon": "co_present", "bg": "#FFCC00", "fg": "#3A2E00"},
    11: {"icon": "person", "bg": "#C7C9CB", "fg": "#2E3538"},
    12: {"icon": "school", "bg": "#4453D6", "fg": "#FFFFFF"},
}

DEFAULT_FACTOR_STYLE = {"icon": "category", "bg": "#1A3A5C", "fg": "#FFFFFF"}


def factor_style(factor_num: int) -> dict[str, str]:
    return FACTOR_STYLE.get(int(factor_num), DEFAULT_FACTOR_STYLE)


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


def factor_icon_html(factor_num: int, size: int = 48, rounded: bool = True) -> str:
    """HTML `<img>` inline con el ícono del factor, o un placeholder si falta."""
    uri = factor_icon_data_uri(factor_num)
    radius = "50%" if rounded else "8px"
    if uri is None:
        return (
            f'<div style="width:{size}px;height:{size}px;border-radius:{radius};'
            f'background:#EEEEEE;display:inline-flex;align-items:center;justify-content:center;'
            f'font-size:{max(10, size // 3)}px;color:#757575;">{factor_num}</div>'
        )
    return (
        f'<img src="{uri}" width="{size}" height="{size}" '
        f'style="border-radius:{radius}; object-fit:cover; border:2px solid #fff; '
        f'box-shadow:0 1px 4px rgba(0,0,0,0.15); vertical-align:middle;" '
        f'alt="Factor {factor_num}" />'
    )
