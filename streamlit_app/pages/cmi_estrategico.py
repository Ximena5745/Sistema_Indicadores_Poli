from datetime import date as _date
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from services.cmi_filters import filter_df_for_cmi_estrategico
    from services.strategic_indicators import (
        NIVEL_COLOR_EXT,
        load_pdi_catalog,
        preparar_pdi_con_cierre,
        load_cierres,
    )
except (ImportError, ModuleNotFoundError):
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))
    from services.strategic_indicators import (
        NIVEL_COLOR_EXT,
        load_pdi_catalog,
        preparar_pdi_con_cierre,
        load_cierres,
    )
    from services.cmi_filters import filter_df_for_cmi_estrategico


def _get_sin_gestion_df():
    """Carga CMI xlsx y retorna DF de indicadores con Plan anual == 3."""
    from services.cmi_filters import load_cmi_worksheet

    df = load_cmi_worksheet()
    if df.empty or "Plan anual" not in df.columns:
        return pd.DataFrame()
    sin_gestion = df[df["Plan anual"] == 3].copy()
    cols = [c for c in ["Id", "Indicador", "Linea"] if c in sin_gestion.columns]
    return sin_gestion[cols] if cols else sin_gestion


CORTE_SEMESTRAL = {
    "Junio": 6,
    "Diciembre": 12,
}
LINEA_COLORS = {
    "Expansión": "#FBAF17",
    "Transformación organizacional": "#42F2F2",
    "Calidad": "#EC0677",
    "Experiencia": "#1FB2DE",
    "Sostenibilidad": "#A6CE38",
    "Educación para toda la vida": "#0F385A",
}

# Usar colores del sistema de diseño (fuente central: docs/core/04_Dashboard.md)
try:
    from streamlit_app.utils.cmi_helpers import linea_color as _linea_color
except ImportError:
    # Fallback si no se puede importar
    def _linea_color(linea: str) -> str:
        import unicodedata
        txt = str(linea or "").strip().lower()
        txt = unicodedata.normalize("NFD", txt)
        txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
        if "expansi" in txt:
            return "#FBAF17"
        if "transform" in txt:
            return "#42F2F2"
        if "calidad" in txt:
            return "#EC0677"
        if "experien" in txt:
            return "#1FB2DE"
        if "sostenib" in txt or "sustentab" in txt:
            return "#A6CE38"
        if "educaci" in txt or "toda la vida" in txt:
            return "#0F385A"
        return "#1A3A5C"


def _default_anio(anios: list[int]) -> int:
    if 2025 in anios:
        return 2025
    if anios:
        return anios[-1]
    return _date.today().year


def _default_corte(anio: int | None) -> str:
    if anio is None:
        return "Diciembre"

    today = _date.today()
    # Años cerrados: siempre corte de diciembre.
    if int(anio) < today.year:
        return "Diciembre"

    # Año no finalizado: usar junio cuando ya pasó el 20 de julio.
    if today > _date(today.year, 7, 20):
        return "Junio"

    return "Diciembre"


def render():
    st.title("CMI Estratégico")
    st.caption(
        "Indicadores del Plan Estratégico (PDI) con cumplimiento de cierre y niveles institucionales."
    )
    # Fase 3: Leer query param 'linea' y filtrar automáticamente
    if hasattr(st, 'query_params') and "linea" in st.query_params:
        linea_from_query = st.query_params["linea"]
        st.session_state["cmi_pdi_linea"] = linea_from_query
        st.experimental_rerun()

    cierres = load_cierres()
    if cierres.empty:
        st.error("No se encontró información de cierres en Resultados Consolidados.xlsx.")
        return

    anios = sorted(
        pd.to_numeric(cierres["Anio"], errors="coerce").dropna().astype(int).unique().tolist()
    )
    if not anios:
        st.error("No hay años disponibles en consolidado de cierres.")
        return

    with st.expander("🔎 Filtros", expanded=False):
        if st.button("Limpiar filtros", key="cmi_pdi_clear"):
            for k in [
                "cmi_pdi_anio",
                "cmi_pdi_mes",
                "cmi_pdi_linea",
                "cmi_pdi_objetivo",
                "cmi_pdi_nombre",
                "_cmi_pdi_last_anio",
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

        _anio_default = _default_anio(anios)
        _fc1, _fc2 = st.columns(2)
        with _fc1:
            anio = st.segmented_control(
                "Año de corte", options=anios, default=_anio_default, key="cmi_pdi_anio"
            )
        with _fc2:
            _corte_default = _default_corte(int(anio) if anio is not None else None)
            corte = st.selectbox(
                "Corte semestral",
                list(CORTE_SEMESTRAL.keys()),
                index=list(CORTE_SEMESTRAL.keys()).index(_corte_default),
                key="cmi_pdi_corte",
            )
        mes = CORTE_SEMESTRAL[corte]

    df = preparar_pdi_con_cierre(int(anio), int(mes))

    # ═══ FILTRO GLOBAL CMI ═══
    # Usar services/cmi_filters.py para aplicar regla de negocio:
    # CMI Estratégico = Indicadores Plan estrategico==1 AND Proyecto!=1
    df = filter_df_for_cmi_estrategico(df, id_column="Id")

    if df.empty:
        st.warning("No hay indicadores de CMI Estratégico para el corte seleccionado.")
        return

    pdi_catalog = load_pdi_catalog()
    lineas = sorted(
        pdi_catalog["Linea"].dropna().astype(str).unique().tolist()
        if not pdi_catalog.empty
        else df["Linea"].dropna().astype(str).unique().tolist()
    )
    _ff1, _ff2, _ff3 = st.columns([1, 2, 2])
    with _ff1:
        linea_sel = st.selectbox("Línea estratégica", ["Todas"] + lineas, key="cmi_pdi_linea")

    if not pdi_catalog.empty:
        obj_pool = (
            pdi_catalog if linea_sel == "Todas" else pdi_catalog[pdi_catalog["Linea"] == linea_sel]
        )
        objetivos = sorted(obj_pool["Objetivo"].dropna().astype(str).unique().tolist())
    else:
        df_obj = df if linea_sel == "Todas" else df[df["Linea"] == linea_sel]
        objetivos = sorted(df_obj["Objetivo"].dropna().astype(str).unique().tolist())

    with _ff2:
        objetivo_sel = st.selectbox(
            "Objetivo estratégico", ["Todos"] + objetivos, key="cmi_pdi_objetivo"
        )
    with _ff3:
        nombre_q = st.text_input(
            "Buscar indicador", key="cmi_pdi_nombre", placeholder="Texto en nombre del indicador"
        )

    if linea_sel != "Todas":
        df = df[df["Linea"] == linea_sel]
    if objetivo_sel != "Todos":
        df = df[df["Objetivo"] == objetivo_sel]
    if nombre_q.strip():
        df = df[df["Indicador"].astype(str).str.contains(nombre_q.strip(), case=False, na=False)]

    if df.empty:
        st.info("No hay registros para los filtros seleccionados.")
        return

    activos = []
    if linea_sel != "Todas":
        activos.append(f"Línea: {linea_sel}")
    if objetivo_sel != "Todos":
        activos.append(f"Objetivo: {objetivo_sel}")
    if nombre_q.strip():
        activos.append(f"Indicador contiene: {nombre_q.strip()}")
    if activos:
        st.caption("Filtros activos: " + " · ".join(activos))

    total = len(df)
    con_dato = int(df["cumplimiento_pct"].notna().sum())
    promedio = float(df["cumplimiento_pct"].mean()) if con_dato else 0.0
    top_nivel = df["Nivel de cumplimiento"].value_counts().idxmax() if total else "Sin dato"
    n_lineas_vis = int(df["Linea"].nunique())
    n_obj_vis = int(df["Objetivo"].nunique())
    n_lineas_cat = int(pdi_catalog["Linea"].nunique()) if not pdi_catalog.empty else n_lineas_vis
    n_obj_cat = int(pdi_catalog["Objetivo"].nunique()) if not pdi_catalog.empty else n_obj_vis

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Indicadores PDI", total)
    k2.metric("Con cumplimiento", con_dato)
    k3.metric("Promedio cumplimiento", f"{promedio:.1f}%")
    k4.metric("Nivel predominante", top_nivel)

    st.caption(f"Corte seleccionado: {corte} {anio}")

    st.caption(
        f"Catálogo PDI: {n_lineas_cat} líneas y {n_obj_cat} objetivos. "
        f"Con indicadores Plan Estratégico=1 en corte: {n_lineas_vis} líneas y {n_obj_vis} objetivos."
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        by_linea = (
            df.groupby("Linea", dropna=False)["cumplimiento_pct"]
            .mean()
            .fillna(0)
            .reset_index()
            .sort_values("cumplimiento_pct", ascending=True)
        )
        by_linea["Linea"] = by_linea["Linea"].astype(str)
        _linea_map = {lin: _linea_color(lin) for lin in by_linea["Linea"].tolist()}
        fig_linea = px.bar(
            by_linea,
            x="cumplimiento_pct",
            y="Linea",
            orientation="h",
            title="Cumplimiento promedio por línea estratégica",
            labels={"cumplimiento_pct": "Cumplimiento (%)", "Linea": "Línea"},
            color="Linea",
            color_discrete_map=_linea_map,
        )
        fig_linea.update_layout(margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
        st.plotly_chart(fig_linea, use_container_width=True, key="cmi_pdi_linea_bar")

    with c2:
        niveles = (
            df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
        )
        niveles.columns = ["Nivel", "Cantidad"]
        fig_niv = px.pie(
            niveles,
            names="Nivel",
            values="Cantidad",
            title="Distribución por nivel",
            color="Nivel",
            color_discrete_map=NIVEL_COLOR_EXT,
            hole=0.45,
        )
        fig_niv.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_niv, use_container_width=True, key="cmi_pdi_nivel_pie")

    sin_gestion_df = _get_sin_gestion_df()
    if not sin_gestion_df.empty:
        st.markdown(
            "<div style='margin-top:2rem;'><b>Indicadores sin gestión (Plan anual = 3)</b></div>",
            unsafe_allow_html=True,
        )
        st.dataframe(sin_gestion_df, hide_index=True, use_container_width=True)

    st.markdown("### Indicadores PDI")
    _cols_pdi = [
        "Id",
        "Indicador",
        "Linea",
        "Objetivo",
        "cumplimiento_pct",
        "Nivel de cumplimiento",
    ]
    if "Meta" in df.columns:
        _cols_pdi.append("Meta")
    if "Ejecucion" in df.columns:
        _cols_pdi.append("Ejecucion")
    if "Sentido" in df.columns:
        _cols_pdi.append("Sentido")
    for extra_col in [
        "Meta_Signo",
        "Meta s",
        "MetaS",
        "Decimales_Meta",
        "Decimales",
        "DecMeta",
        "Ejecucion_Signo",
        "Ejecución s",
        "Ejecucion s",
        "Ejecucion_s",
        "EjecS",
        "Decimales_Ejecucion",
        "DecimalesEje",
        "DecEjec",
    ]:
        if extra_col in df.columns:
            _cols_pdi.append(extra_col)
    _cols_pdi += ["Anio", "Mes", "Fecha"]
    tabla = df[[c for c in _cols_pdi if c in df.columns]].copy()
    tabla = tabla.rename(
        columns={
            "cumplimiento_pct": "Cumplimiento (%)",
            "Nivel de cumplimiento": "Nivel",
            "Anio": "Año cierre",
            "Mes": "Mes cierre",
            "Meta": "Meta",
            "Ejecucion": "Ejecución",
        }
    )
    tabla["Cumplimiento (%)"] = pd.to_numeric(tabla["Cumplimiento (%)"], errors="coerce").round(1)
    tabla = formatear_meta_ejecucion_df(tabla, meta_col="Meta", ejec_col="Ejecución")
    tabla = tabla.sort_values(
        (
            ["Linea", "Objetivo", "Id"]
            if all(c in tabla.columns for c in ["Linea", "Objetivo"])
            else ["Id"]
        ),
        na_position="last",
    )

    # Color de fondo por Nivel en columna Nivel
    _NIVEL_BG_CMI = {
        "Peligro": "#FFCDD2",
        "Alerta": "#FEF3D0",
        "Cumplimiento": "#E8F5E9",
        "Sobrecumplimiento": "#DCE6FF",
        "No aplica": "#ECEFF1",
        "Pendiente de reporte": "#F5F5F5",
    }
    _NIVEL_ICONS_CMI = {
        "Peligro": "🚩",
        "Alerta": "⚑",
        "Cumplimiento": "🏁",
        "Sobrecumplimiento": "🎌",
        "No aplica": "🏴",
        "Pendiente de reporte": "🏳️",
    }
    if "Nivel" in tabla.columns:
        tabla["Nivel"] = tabla["Nivel"].apply(
            lambda n: f'{_NIVEL_ICONS_CMI.get(str(n), "")} {n}' if pd.notna(n) else n
        )
    if "Linea" in tabla.columns:
        tabla["Color Línea"] = tabla["Linea"].apply(lambda l: _linea_color(str(l or "")))

    _cfg_pdi = {
        "Id": st.column_config.TextColumn("ID", width="small"),
        "Indicador": st.column_config.TextColumn("Indicador", width="large"),
        "Linea": st.column_config.TextColumn("Línea", width="medium"),
        "Objetivo": st.column_config.TextColumn("Objetivo", width="large"),
        "Nivel": st.column_config.TextColumn("Nivel", width="medium"),
        "Cumplimiento (%)": st.column_config.NumberColumn(
            "Cumplimiento %", format="%.1f", width="small"
        ),
        "Meta": st.column_config.TextColumn("Meta", width="small"),
        "Ejecución": st.column_config.TextColumn("Ejecución", width="small"),
        "Sentido": st.column_config.TextColumn("Sentido", width="small"),
        "Año cierre": st.column_config.NumberColumn("Año", format="%d", width="small"),
        "Mes cierre": st.column_config.NumberColumn("Mes", format="%d", width="small"),
        "Fecha": st.column_config.DatetimeColumn("Fecha", width="small"),
    }

    # Renderizar indicadores PDI por Línea: título con color y tarjetas por Objetivo
    def _render_indicator_table(df_obj: pd.DataFrame) -> str:
        """Retorna HTML de una tabla compacta con columnas Indicador, Meta, Ejecución, Cumplimiento."""
        cols = [
            c for c in ["Indicador", "Meta", "Ejecución", "Cumplimiento (%)"] if c in df_obj.columns
        ]
        if df_obj.empty:
            return "<div style='padding:8px'>No hay indicadores para este objetivo.</div>"

        nivel_flag_colors = {
            "Peligro": "#C62828",
            "Alerta": "#F9A825",
            "Cumplimiento": "#2E7D32",
            "Sobrecumplimiento": "#6699FF",
            "No aplica": "#616161",
            "Pendiente de reporte": "#9E9E9E",
        }

        def _nivel_limpio(raw) -> str:
            txt = str(raw or "").strip()
            if not txt:
                return ""
            # Si ya viene con icono (ej. "🏁 Cumplimiento"), remover primer token.
            parts = txt.split(" ", 1)
            if len(parts) == 2 and parts[0] in {
                "🔴",
                "🟡",
                "🟢",
                "🔵",
                "⚫",
                "⚪",
                "🚩",
                "⚑",
                "🏁",
                "🎌",
                "🏴",
                "🏳️",
            }:
                return parts[1].strip()
            return txt

        def _cumplimiento_display(row) -> str:
            val = pd.to_numeric(row.get("Cumplimiento (%)"), errors="coerce")
            nivel = _nivel_limpio(row.get("Nivel", ""))
            color = nivel_flag_colors.get(nivel, "#9E9E9E")
            icon = f"<span style='color:{color};font-weight:700'>⚑</span>"
            if pd.isna(val):
                return f"{icon} -".strip()
            return f"{icon} {float(val):.1f}%".strip()

        html = ["<table style='width:100%;border-collapse:collapse;font-size:0.9rem'>"]
        # header
        html.append(
            "<tr style='background:#e9f7fb;color:#033;'><th style='padding:8px;border:1px solid #d0e9ef;text-align:left'>Indicador</th>"
        )
        for c in cols[1:]:
            html.append(
                f"<th style='padding:8px;border:1px solid #d0e9ef;text-align:center'>{c}</th>"
            )
        html.append("</tr>")
        # rows
        for _, r in df_obj.iterrows():
            html.append("<tr>")
            html.append(
                f"<td style='padding:8px;border:1px solid #eef7fb'>{_escape(str(r.get('Indicador','')))}</td>"
            )
            for c in cols[1:]:
                if c == "Cumplimiento (%)":
                    display = _cumplimiento_display(r)
                else:
                    val = r.get(c, "")
                    display = f"{val}" if pd.notna(val) else ""
                align = "center"
                html.append(
                    f"<td style='padding:8px;border:1px solid #eef7fb;text-align:{align}'>{display}</td>"
                )
            html.append("</tr>")
        html.append("</table>")
        return "".join(html)

    # Ordenar líneas según catálogo (asegurar las seis líneas ordenadas)
    ordered_lineas = [l for l in LINEA_COLORS.keys() if l in tabla["Linea"].unique()] + [
        l for l in tabla["Linea"].unique() if l not in LINEA_COLORS.keys()
    ]
    from html import escape as _escape

    # Nuevo render compacto y contextualizado de líneas estratégicas
    st.markdown("""
    <style>
    .cmi-card {
        background: #fff;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 18px;
        padding: 0;
        display: flex;
        align-items: stretch;
        transition: box-shadow 0.2s;
    }
    .cmi-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    }
    .cmi-card-color {
        width: 12px;
        border-radius: 12px 0 0 12px;
        margin-right: 0;
    }
    .cmi-card-content {
        flex: 1;
        padding: 18px 24px 18px 18px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .cmi-card-title {
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 4px;
        color: #222;
    }
    .cmi-card-desc {
        font-size: 1rem;
        color: #555;
        margin-bottom: 10px;
    }
    .cmi-card-stats {
        display: flex;
        gap: 24px;
        margin-bottom: 0;
    }
    .cmi-card-stat {
        font-size: 1.05rem;
        color: #333;
        background: #f7fafc;
        border-radius: 6px;
        padding: 4px 12px;
        margin-right: 0;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .cmi-card-value {
        font-weight: 700;
        color: #1976d2;
        margin-left: 4px;
    }
    .cmi-card-cumplimiento {
        font-size: 1.15rem;
        font-weight: 700;
        color: #fff;
        background: linear-gradient(90deg, #1976d2 60%, #43a047 100%);
        border-radius: 8px;
        padding: 6px 18px;
        margin-left: auto;
        align-self: flex-end;
        box-shadow: 0 1px 4px rgba(25,118,210,0.08);
    }
    </style>
    """, unsafe_allow_html=True)

    for linea in ordered_lineas:
        color = LINEA_COLORS.get(linea, _linea_color(linea))
        df_line = tabla[tabla["Linea"] == linea].copy()
        if df_line.empty:
            continue
        n_indicadores = len(df_line)
        n_objetivos = df_line["Objetivo"].nunique()
        n_metas = df_line["Meta"].nunique() if "Meta" in df_line.columns else "-"
        cumplimiento = df_line["Cumplimiento (%)"].mean()
        cumplimiento_str = f"{cumplimiento:.1f}%" if not pd.isna(cumplimiento) else "-"
        desc = f"{n_indicadores} indicadores · {n_objetivos} objetivos · {n_metas} metas"
        st.markdown(f"""
        <div class='cmi-card'>
            <div class='cmi-card-color' style='background:{color};'></div>
            <div class='cmi-card-content'>
                <div class='cmi-card-title'>{_escape(linea)}</div>
                <div class='cmi-card-desc'>{desc}</div>
                <div class='cmi-card-stats'>
                    <div class='cmi-card-stat'>Indicadores <span class='cmi-card-value'>{n_indicadores}</span></div>
                    <div class='cmi-card-stat'>Objetivos <span class='cmi-card-value'>{n_objetivos}</span></div>
                    <div class='cmi-card-stat'>Metas <span class='cmi-card-value'>{n_metas}</span></div>
                </div>
                <div class='cmi-card-cumplimiento'>Cumplimiento: {cumplimiento_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Render jerárquico: Objetivos -> Metas/Indicadores
        objetivos = df_line["Objetivo"].dropna().unique().tolist()
        for objetivo in objetivos:
            with st.expander(f"🎯 {objetivo}"):
                df_obj = df_line[df_line["Objetivo"] == objetivo].copy()
                # Agrupar por Meta si existe columna Meta
                if "Meta" in df_obj.columns:
                    metas = df_obj["Meta"].dropna().unique().tolist()
                    for meta in metas:
                        st.markdown(f"<div style='font-weight:600;margin-bottom:4px;color:#1976d2'>Meta: {_escape(str(meta))}</div>", unsafe_allow_html=True)
                        df_meta = df_obj[df_obj["Meta"] == meta].copy()
                        # Mostrar tabla de indicadores para la meta
                        st.dataframe(
                            df_meta[[c for c in ["Indicador", "Ejecución", "Cumplimiento (%)", "Nivel"] if c in df_meta.columns]],
                            hide_index=True,
                            use_container_width=True,
                        )
                else:
                    # Si no hay columna Meta, mostrar todos los indicadores del objetivo
                    st.dataframe(
                        df_obj[[c for c in ["Indicador", "Ejecución", "Cumplimiento (%)", "Nivel"] if c in df_obj.columns]],
                        hide_index=True,
                        use_container_width=True,
                    )
