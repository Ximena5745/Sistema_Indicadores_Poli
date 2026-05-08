"""filter_panel.py — Sistema Global de Filtros Unificado."""

from __future__ import annotations

from itertools import cycle
from typing import Any

import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# CSS GLOBAL — inyectado UNA VEZ por sesión
# NO contiene ningún wrapper HTML; sólo estilos para widgets nativos
# ──────────────────────────────────────────────────────────────────────────────

_FILTER_CSS = """<style>
/* ── Labels nativos de widgets ─────────────────────────────────── */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] > span {
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    color: #0E7490 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    margin-bottom: 4px !important;
    line-height: 1.3 !important;
}

/* ── Selectbox ──────────────────────────────────────────────────── */
[data-baseweb="select"] > div:first-child {
    border: 1.5px solid #67E8F9 !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    min-height: 40px !important;
    font-size: 0.88rem !important;
    transition: border-color 0.18s, box-shadow 0.18s;
}
[data-baseweb="select"] > div:first-child:focus-within {
    border-color: #0E7490 !important;
    box-shadow: 0 0 0 2.5px rgba(14, 116, 144, 0.15) !important;
}

/* ── Text input ─────────────────────────────────────────────────── */
.stTextInput input {
    border: 1.5px solid #67E8F9 !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    min-height: 40px !important;
    font-size: 0.88rem !important;
    padding: 0 10px !important;
}
.stTextInput input:focus {
    border-color: #0E7490 !important;
    box-shadow: 0 0 0 2.5px rgba(14, 116, 144, 0.15) !important;
}

/* ── Pills ──────────────────────────────────────────────────────── */
[data-testid="stPills"] { gap: 6px !important; }
[data-testid="stPillsOption"] {
    font-size: 0.83rem !important;
    padding: 5px 14px !important;
    border-radius: 999px !important;
    border: 1.5px solid #67E8F9 !important;
}
[data-testid="stPillsOption"][aria-pressed="true"] {
    background: #0E7490 !important;
    color: #FFFFFF !important;
    border-color: #0E7490 !important;
}

/* ── Segmented control ──────────────────────────────────────────── */
[data-testid="stSegmentedControl"] button {
    font-size: 0.83rem !important;
    border-radius: 8px !important;
}
[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
    background: linear-gradient(135deg, #0E7490 0%, #06B6D4 100%) !important;
    color: #FFFFFF !important;
    border-color: #0E7490 !important;
    box-shadow: 0 2px 8px rgba(14, 116, 144, 0.30) !important;
}

/* ── Quitar margen inferior de widgets dentro del panel ─────────── */
.stSelectbox,
[data-testid="stPills"],
[data-testid="stSegmentedControl"],
.stTextInput {
    margin-bottom: 0 !important;
}

/* ── Columnas compactas ─────────────────────────────────────────── */
[data-testid="column"] {
    padding-top: 0 !important;
    padding-bottom: 2px !important;
}
</style>"""


def inject_filter_styles() -> None:
    """Inyecta el CSS una vez por sesión."""
    if st.session_state.get("_uf_styles_injected"):
        return
    st.markdown(_FILTER_CSS, unsafe_allow_html=True)
    st.session_state["_uf_styles_injected"] = True


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNOS
# ──────────────────────────────────────────────────────────────────────────────


def _build_options(filt: dict) -> list:
    raw = list(filt.get("options", []))
    if filt.get("include_all", True):
        all_label = filt.get("all_label", "Todos")
        raw = [o for o in raw if str(o) != str(all_label)]
        return [all_label] + raw
    return raw


def _resolve_default(filt: dict, options: list) -> Any:
    default = filt.get("default")
    if default is None:
        return options[0] if options else None
    if default not in options:
        return options[0] if options else default
    return default


def _render_widget(filt: dict, key_prefix: str) -> Any:
    ftype = filt.get("type", "selectbox")
    label = filt["label"]
    key = f"{key_prefix}_{filt['key']}"
    options = _build_options(filt)
    default = _resolve_default(filt, options)

    if ftype == "segmented_control":
        val = st.segmented_control(label, options=options, default=default, key=key)
        return val if val is not None else default

    if ftype == "pills":
        val = st.pills(label, options=options, default=default, key=key)
        return val if val is not None else default

    if ftype == "text":
        return st.text_input(label, key=key, placeholder=filt.get("placeholder", ""))

    if ftype == "multiselect":
        return st.multiselect(label, options=options, default=filt.get("default", []), key=key)

    # selectbox
    idx = options.index(default) if default in options else 0
    return st.selectbox(label, options=options, index=idx, key=key)


# ──────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL PÚBLICA
# ──────────────────────────────────────────────────────────────────────────────


def render_filter_panel(
    filters: list[dict],
    title: str = "Filtros",
    key_prefix: str = "fp",
    n_cols: int | None = None,
    show_reset: bool = False,
    reset_keys: list[str] | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    """Renderiza un panel de filtros con contenedor nativo de Streamlit.

    Usa ``st.container(border=True)`` para el card — sin ningún
    ``st.markdown()`` de envoltura que genere bloques vacíos.

    Parámetros
    ----------
    filters : list[dict]
        Claves válidas por filtro:
        ``key``, ``label``, ``type`` (selectbox|segmented_control|pills|text|multiselect),
        ``options``, ``default``, ``include_all``, ``all_label``, ``placeholder``
    title : str
        Título del panel (aparece como encabezado dentro del contenedor).
    key_prefix : str
        Prefijo para las session_state keys — debe ser único por página.
    n_cols : int | None
        Columnas del grid. Si None: min(len(filters), 4).
    show_reset : bool
        Muestra botón "Limpiar" al final de la fila.
    reset_keys : list[str] | None
        Keys a limpiar; si None usa las keys auto-generadas del panel.
    summary : str | None
        Texto de caption debajo del panel.

    Retorna
    -------
    dict[str, Any]  — ``{filter_key: selected_value}``
    """
    inject_filter_styles()

    actual_n_cols = n_cols or min(len(filters), 4)
    selections: dict[str, Any] = {}

    with st.container(border=True):
        if title:
            st.markdown(f"🔍 **{title}**")

        if show_reset:
            cols = st.columns(actual_n_cols + 1, gap="small")
            filter_cols = cols[:actual_n_cols]
            reset_col = cols[actual_n_cols]
        else:
            cols = st.columns(actual_n_cols, gap="small")
            filter_cols = cols

        col_iter = cycle(filter_cols)
        for filt in filters:
            with next(col_iter):
                selections[filt["key"]] = _render_widget(filt, key_prefix)

        if show_reset:
            with reset_col:
                _auto_reset_keys = reset_keys or [f"{key_prefix}_{f['key']}" for f in filters]
                st.write("")  # alineación vertical con los widgets
                if st.button("↺ Limpiar", key=f"{key_prefix}_reset_btn", use_container_width=True):
                    for k in _auto_reset_keys:
                        st.session_state.pop(k, None)
                    st.rerun()

    if summary:
        st.caption(summary)

    return selections


def build_active_summary(
    selections: dict[str, Any],
    filters: list[dict],
    labels_override: dict[str, str] | None = None,
) -> str:
    """Construye texto de resumen de filtros activos (excluye valores 'Todos')."""
    parts = []
    for filt in filters:
        key = filt["key"]
        val = selections.get(key)
        if val is None:
            continue
        all_label = filt.get("all_label", "Todos")
        if filt.get("include_all", True) and str(val) == str(all_label):
            continue
        label = (labels_override or {}).get(key, filt.get("label", key))
        parts.append(f"{label}: {val}")
    return " · ".join(parts) if parts else ""

