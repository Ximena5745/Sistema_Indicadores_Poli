"""filters.py — Wrapper de compatibilidad hacia render_filter_panel.

render_filters() traduce el formato de config legado al nuevo formato de
render_filter_panel, sin ningún HTML envolvente.  Páginas nuevas deben
importar render_filter_panel directamente.
"""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.filter_panel import render_filter_panel, inject_filter_styles


def render_filters(
    data,
    config,
    key_prefix="filter",
    columns_per_row=3,
    collapsible: bool = False,
    collapsed_by_default: bool = True,
    compact: bool = True,
):
    """Renderiza filtros reutilizables usando render_filter_panel.

    Convierte el formato de config legado ``{key: {label, options, default, include_all}}``
    al formato de filtros unificado.  Sin HTML envolvente.

    Retorna: dict ``{key: valor_seleccionado}``
    """
    del data, collapsible, collapsed_by_default, compact  # parámetros legados ignorados

    filters = []
    for key, conf in config.items():
        filt = {
            "key": key,
            "label": conf.get("label", key),
            "type": "selectbox",
            "options": list(conf.get("options", [])),
            "include_all": conf.get("include_all", True),
            "all_label": conf.get("all_label", "Todos"),
        }
        if "default" in conf:
            filt["default"] = conf["default"]
        filters.append(filt)

    return render_filter_panel(
        filters=filters,
        title="Filtros",
        key_prefix=key_prefix,
        n_cols=min(columns_per_row, len(filters)) if filters else 1,
    )
