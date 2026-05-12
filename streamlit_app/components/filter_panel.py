"""filter_panel.py — Sistema Global de Filtros Unificado."""

from __future__ import annotations

from typing import Any

import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# CSS GLOBAL — inyectado UNA VEZ por sesión
# NO contiene ningún wrapper HTML; sólo estilos para widgets nativos
# ──────────────────────────────────────────────────────────────────────────────

_FILTER_CSS = """<style>
/* ── Tokens ─────────────────────────────────────────────────────── */
:root {
    --fp-primary:        #0F3A6D;
    --fp-primary-hover:  #1D4A86;
    --fp-accent-a:       #0077CC;
    --fp-accent-b:       #00B4FF;
    --fp-sel-start:      #0077CC;
    --fp-sel-end:        #00B4FF;
    --fp-sel-border:     #0077CC;
    --fp-primary-soft:   #E2EEF9;
    --fp-border:         #A8C4E0;
    --fp-input-bg:       #F0F6FF;
    --fp-text:           #0C1A2E;
    --fp-text-muted:     #4A6580;
    --fp-surface:        #FFFFFF;
    --fp-container-bg:   linear-gradient(135deg, #EFF6FF 0%, #F0F9FF 60%, #EEF4FB 100%);
    --fp-container-bdr:  #93C5FD;
    --fp-shadow:         0 4px 18px rgba(15,58,109,0.10), 0 1px 4px rgba(15,58,109,0.06);
}

/* ── Contenedor principal: gradiente + sombra suave ─────────────── */
html body [data-testid="stContainer"] {
    background: var(--fp-container-bg) !important;
    border: 1.5px solid var(--fp-container-bdr) !important;
    border-radius: 14px !important;
    box-shadow: var(--fp-shadow) !important;
    padding: 8px 12px 6px 12px !important;
}

/* ── Caption "Filtros activos" ───────────────────────────────────── */
html body [data-testid="stContainer"] [data-testid="stCaptionContainer"] p {
    font-size: 0.7rem !important;
    font-weight: 800 !important;
    color: var(--fp-accent-a) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    margin-bottom: 2px !important;
}

/* ── Labels ─────────────────────────────────────────────────────── */
html body [data-testid="stWidgetLabel"] p,
html body [data-testid="stWidgetLabel"] label,
html body [data-testid="stWidgetLabel"] > div > p,
html body .stSelectbox label,
html body .stMultiSelect label {
    font-size: 0.7rem !important;
    font-weight: 800 !important;
    color: var(--fp-accent-a) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin-bottom: 2px !important;
    line-height: 1.25 !important;
}

/* ── Selectbox / Multiselect ─────────────────────────────────────── */
html body [data-baseweb="select"] > div {
    border: 1.5px solid var(--fp-border) !important;
    border-left: 3px solid var(--fp-accent-a) !important;
    border-radius: 9px !important;
    background: var(--fp-input-bg) !important;
    min-height: 34px !important;
    box-shadow: 0 1px 4px rgba(15,58,109,0.07) !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
html body [data-baseweb="select"] > div:focus-within {
    border-color: var(--fp-accent-a) !important;
    border-left-color: var(--fp-accent-b) !important;
    box-shadow: 0 0 0 3px rgba(0,119,204,0.18) !important;
}
html body [data-baseweb="select"] span {
    font-size: 0.87rem !important;
    font-weight: 500 !important;
    color: var(--fp-text) !important;
}
html body [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
    border: 1.5px solid var(--fp-border) !important;
    border-left: 3px solid var(--fp-accent-a) !important;
    border-radius: 9px !important;
    background: var(--fp-input-bg) !important;
}

/* ── Text input ─────────────────────────────────────────────────── */
html body [data-testid="stTextInput"] input,
html body .stTextInput input {
    border: 1.5px solid var(--fp-border) !important;
    border-left: 3px solid var(--fp-accent-a) !important;
    border-radius: 9px !important;
    background: var(--fp-input-bg) !important;
    min-height: 36px !important;
    font-size: 0.87rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
html body [data-testid="stTextInput"] input:focus {
    border-color: var(--fp-accent-a) !important;
    box-shadow: 0 0 0 3px rgba(0,119,204,0.18) !important;
    outline: none !important;
}

/* ── Dropdown popup ─────────────────────────────────────────────── */
html body [data-baseweb="popover"] [data-baseweb="menu"],
html body [data-baseweb="popover"] ul {
    border-radius: 10px !important;
    border: 1.5px solid var(--fp-accent-a) !important;
    box-shadow: 0 6px 24px rgba(15,58,109,0.16) !important;
}
html body [data-baseweb="option"]:hover,
html body [data-baseweb="option"][aria-selected="true"] {
    background: rgba(0,119,204,0.10) !important;
    color: var(--fp-primary) !important;
}

/* ── Pills ──────────────────────────────────────────────────────── */
html body [data-testid="stPillsOption"],
html body button[data-testid="stPillsOption"],
html body [data-testid="stPills"] button,
html body div[data-baseweb="pills"] button,
html body .stContainer [data-testid="stPills"] button,
html body .stContainer div[data-baseweb="pills"] button {
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    padding: 3px 13px !important;
    border-radius: 999px !important;
    border: 1.5px solid var(--fp-border) !important;
    background: #DBEAFE !important;
    color: var(--fp-accent-a) !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(0,119,204,0.10) !important;
}
html body [data-testid="stPillsOption"][aria-pressed="true"],
html body button[data-testid="stPillsOption"][aria-pressed="true"],
html body [data-testid="stPills"] button[aria-pressed="true"],
html body div[data-baseweb="pills"] button[aria-pressed="true"],
html body .stContainer [data-testid="stPills"] button[aria-pressed="true"],
html body .stContainer div[data-baseweb="pills"] button[aria-pressed="true"] {
    background: linear-gradient(135deg, var(--fp-sel-start) 0%, var(--fp-sel-end) 100%) !important;
    color: #FFFFFF !important;
    border-color: var(--fp-sel-border) !important;
    box-shadow: 0 3px 10px rgba(0,119,204,0.40) !important;
    font-weight: 800 !important;
}
html body [data-testid="stPills"] button[aria-pressed="true"] > div,
html body [data-testid="stPills"] button[aria-pressed="true"] > span,
html body div[data-baseweb="pills"] button[aria-pressed="true"] > div,
html body div[data-baseweb="pills"] button[aria-pressed="true"] > span {
    color: #FFFFFF !important;
}

/* ── Segmented control ──────────────────────────────────────────── */
html body [data-testid="stSegmentedControl"] > div,
html body div[data-baseweb="segmented-control"] {
    background: #DBEAFE !important;
    border: 1.5px solid var(--fp-border) !important;
    border-radius: 10px !important;
    padding: 2px !important;
}
html body [data-testid="stSegmentedControl"] button,
html body div[data-baseweb="segmented-control"] button,
html body [role="radiogroup"] button {
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    border-radius: 7px !important;
    border: 1px solid transparent !important;
    background: #F4F8FD !important;
    color: var(--fp-accent-a) !important;
    transition: all 0.15s ease !important;
    min-height: 34px !important;
    padding: 0.35rem 0.85rem !important;
}
html body [data-testid="stSegmentedControl"] button:hover,
html body div[data-baseweb="segmented-control"] button:hover,
html body [role="radiogroup"] button:hover {
    color: var(--fp-primary) !important;
    background: var(--fp-primary-soft) !important;
}
html body [data-testid="stSegmentedControl"] button[aria-pressed="true"],
html body [data-testid="stSegmentedControl"] button[kind="segmented_controlActive"],
html body [data-testid="stSegmentedControl"] button[data-testid="stBaseButton-segmented_controlActive"],
html body div[data-baseweb="segmented-control"] button[aria-pressed="true"],
html body div[data-baseweb="segmented-control"] button[kind="segmented_controlActive"],
html body div[data-baseweb="segmented-control"] button[data-testid="stBaseButton-segmented_controlActive"],
html body [role="radiogroup"] button[aria-pressed="true"],
html body [role="radiogroup"] button[kind="segmented_controlActive"],
html body [role="radiogroup"] button[data-testid="stBaseButton-segmented_controlActive"] {
    background: linear-gradient(135deg, var(--fp-sel-start) 0%, var(--fp-sel-end) 100%) !important;
    color: #FFFFFF !important;
    border-color: var(--fp-sel-border) !important;
    box-shadow: 0 3px 10px rgba(0,119,204,0.28) !important;
    font-weight: 800 !important;
}
html body [data-testid="stSegmentedControl"] button[aria-pressed="true"] > div,
html body [data-testid="stSegmentedControl"] button[aria-pressed="true"] > span,
html body [data-testid="stSegmentedControl"] button[kind="segmented_controlActive"] > div,
html body [data-testid="stSegmentedControl"] button[kind="segmented_controlActive"] > span,
html body [data-testid="stSegmentedControl"] button[data-testid="stBaseButton-segmented_controlActive"] > div,
html body [data-testid="stSegmentedControl"] button[data-testid="stBaseButton-segmented_controlActive"] > span,
html body div[data-baseweb="segmented-control"] button[aria-pressed="true"] > div,
html body div[data-baseweb="segmented-control"] button[aria-pressed="true"] > span,
html body [role="radiogroup"] button[kind="segmented_controlActive"] > div,
html body [role="radiogroup"] button[kind="segmented_controlActive"] > span,
html body [role="radiogroup"] button[data-testid="stBaseButton-segmented_controlActive"] > div,
html body [role="radiogroup"] button[data-testid="stBaseButton-segmented_controlActive"] > span {
    color: #FFFFFF !important;
}
html body [role="radiogroup"] button {
    box-shadow: none !important;
}

html body [data-testid="stSegmentedControl"],
html body [data-testid="stPills"],
html body [role="radiogroup"] {
    --primary-color: var(--fp-primary) !important;
}

/* ── Compactar widgets ──────────────────────────────────────────── */
html body .stSelectbox,
html body .stTextInput,
html body .stMultiSelect,
html body [data-testid="stPills"],
html body [data-testid="stSegmentedControl"] {
    margin-bottom: 0 !important;
    margin-top: 0 !important;
    padding-bottom: 0 !important;
    padding-top: 0 !important;
}
html body .stContainer [data-testid="stVerticalBlock"] {
    gap: 0.04rem !important;
    margin: 0 !important;
    padding: 0 !important;
}
html body .stContainer [data-testid="stVerticalBlock"] > div { gap: 0.04rem !important; }
html body .stContainer [data-testid="stBlock"] { margin-bottom: 0.04rem !important; padding: 0 !important; }
html body .stContainer .stSelectbox,
html body .stContainer .stTextInput,
html body .stContainer [data-testid="stPills"],
html body .stContainer [data-testid="stSegmentedControl"] {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
html body .stColumns { gap: 0.08rem !important; }
html body .stColumn { padding: 0 !important; }

/* ── Botón reset ─────────────────────────────────────────────────── */
html body [data-testid="stButton"] > button {
    border: 1.5px solid var(--fp-border) !important;
    background: var(--fp-input-bg) !important;
    color: var(--fp-accent-a) !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
}
html body [data-testid="stButton"] > button:hover {
    border-color: var(--fp-accent-a) !important;
    background: var(--fp-primary-soft) !important;
    color: var(--fp-primary) !important;
    box-shadow: 0 2px 8px rgba(0,119,204,0.18) !important;
}

html body [data-testid="stContainer"] [data-testid="stVerticalBlock"],
html body .stColumn { gap: 0 !important; }
html body [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
</style>"""


def inject_filter_styles() -> None:
    """Inyecta el CSS en cada render de página.

    IMPORTANTE: NO usar session_state guard aquí.
    En Streamlit multi-page, session_state persiste entre páginas pero
    el DOM se limpia en cada navegación — el CSS debe reinyectarse siempre.
    """
    st.markdown(_FILTER_CSS, unsafe_allow_html=True)


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

    _auto_reset_keys = reset_keys or [f"{key_prefix}_{f['key']}" for f in filters]

    with st.container(border=True):
        if title:
            st.caption(f"🔍 {title}")

        # Partir filtros en filas de actual_n_cols — una fila = un st.columns()
        rows = [filters[i : i + actual_n_cols] for i in range(0, len(filters), actual_n_cols)]
        for row_idx, row_filters in enumerate(rows):
            is_last = row_idx == len(rows) - 1
            
            # Calcular ancho de columnas para ESTA fila específicamente
            if is_last and show_reset:
                # Última fila CON botón reset: n_filtros en esta fila + columna reset
                row_col_widths = [1] * len(row_filters) + [0.35]
            elif show_reset and not is_last:
                # Filas intermedias CON botón reset: mantener consistencia visual
                row_col_widths = [1] * actual_n_cols + [0.35]
            elif is_last and not show_reset:
                # Última fila SIN botón: solo los filtros que hay
                row_col_widths = [1] * len(row_filters)
            else:
                # Filas intermedias SIN botón
                row_col_widths = [1] * actual_n_cols
            
            row_cols = st.columns(row_col_widths, gap="xxsmall")
            for col_i, filt in enumerate(row_filters):
                with row_cols[col_i]:
                    selections[filt["key"]] = _render_widget(filt, key_prefix)
            
            # Botón reset en la última columna de la última fila
            if is_last and show_reset:
                with row_cols[-1]:
                    st.write("")  # alineación vertical
                    if st.button("↺", key=f"{key_prefix}_reset_btn",
                                 use_container_width=True, help="Restablecer filtros"):
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

