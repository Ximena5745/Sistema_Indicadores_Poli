import streamlit as st


def render_filters(data, config, key_prefix="filter", columns_per_row=3, collapsible: bool = False, collapsed_by_default: bool = True):
    """Renderiza filtros reutilizables.

    Args:
        data: no usado, mantenido para compatibilidad.
        config: dict con definición de filtros (label, options, default, include_all).
        key_prefix: prefijo para keys de Streamlit.
        columns_per_row: cuántos filtros mostrar por fila.
        collapsible: si True muestra los primeros `columns_per_row` filtros en línea y el resto dentro de un `st.expander`.
        collapsed_by_default: si el expander inicia colapsado cuando `collapsible=True`.

    Devuelve: dict con las selecciones.
    """
    del data

    selections = {}
    items = list(config.items())

    if collapsible and len(items) > columns_per_row:
        # Mostrar primeros N filtros en línea, el resto en un expander
        primary = items[:columns_per_row]
        secondary = items[columns_per_row:]

        # Render primary inline
        cols = st.columns(len(primary))
        for col, (key, conf) in zip(cols, primary):
            with col:
                selections[key] = _render_single_filter(conf, key_prefix, key)

        # Render secondary inside expander
        with st.expander("🔎 Filtros avanzados", expanded=not collapsed_by_default):
            for start in range(0, len(secondary), columns_per_row):
                row_items = secondary[start:start + columns_per_row]
                cols = st.columns(min(columns_per_row, len(row_items)))
                for col, (key, conf) in zip(cols, row_items):
                    with col:
                        selections[key] = _render_single_filter(conf, key_prefix, key)

    else:
        # Render all inline in rows
        for start in range(0, len(items), columns_per_row):
            cols = st.columns(min(columns_per_row, len(items) - start))
            row_items = items[start:start + columns_per_row]

            for col, (key, conf) in zip(cols, row_items):
                with col:
                    selections[key] = _render_single_filter(conf, key_prefix, key)

    return selections


def _render_single_filter(conf: dict, key_prefix: str, key: str):
    """Helper: renderiza un solo filtro y devuelve el valor seleccionado."""
    raw_options = list(conf.get("options", []))
    include_all = conf.get("include_all", True)
    all_label = conf.get("all_label", "Todos")
    options = ([all_label] if include_all else []) + raw_options

    if not options:
        st.selectbox(conf["label"], ["Sin opciones"], disabled=True, key=f"{key_prefix}_{key}")
        return None

    default_value = conf.get("default", options[0])
    if default_value not in options:
        default_value = options[0]

    return st.selectbox(
        conf["label"],
        options,
        index=options.index(default_value),
        key=f"{key_prefix}_{key}",
        format_func=lambda x, ia=include_all, al=all_label, conf=conf: str(conf.get("all_display", "— Todos —")) if ia and x == al else str(x),
    )
