from datetime import date as _date
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.services.strategic_indicators import (
    NIVEL_COLOR_EXT,
    load_pdi_catalog,
    preparar_pdi_con_cierre,
    load_cierres,
)
from services.data_loader import cargar_acciones_mejora
from streamlit_app.styles.design_system import get_line_color
from streamlit_app.components.renderers import render_exec_summary, set_global_palette, render_echarts, actions_table, render_alert_strip, render_narrative_panel
import math
import json

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


def _linea_color(linea: str) -> str:
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
    if "sostenib" in txt:
        return "#A6CE38"
    if "educaci" in txt or "toda la vida" in txt:
        return "#0F385A"
    # Fallback al sistema de diseño (si existe mapeo global)
    return get_line_color(linea)


# ─── Pesos por línea estratégica para el ISI ─────────────────────────────────
# Ajustables según prioridad institucional; suman 1.0
_PESOS_LINEA: dict[str, float] = {
    "expansion":                      0.20,
    "transformacion organizacional":   0.18,
    "calidad":                         0.22,
    "experiencia":                     0.15,
    "sostenibilidad":                  0.15,
    "educacion para toda la vida":     0.10,
}
_PESO_DEFAULT = 1.0  # peso neutro si la línea no está en el mapa

# Bonus por sobrecumplimiento y penalización por peligro (puntos sobre 100)
_BONUS_SOBRE = 5.0
_PEN_PELIGRO = -8.0
_PEN_ALERTA  = -3.0


def _nm_linea(s: str) -> str:
    s = str(s or "").strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s


def _calcular_isi(df: pd.DataFrame) -> tuple[float, pd.DataFrame, pd.DataFrame]:
    """Calcula el Índice de Salud Institucional (0-100).

    Retorna (isi, df_por_linea, df_por_objetivo).
    Fórmula:
      1. Cumplimiento promedio ponderado por línea (escala 0-100)
      2. Ajustes: bonus por sobrecumplimiento, penalización por peligro/alerta
      3. Clip [0, 100]
    """
    if df.empty or "cumplimiento_pct" not in df.columns:
        return 0.0, pd.DataFrame(), pd.DataFrame()

    df_v = df[df["cumplimiento_pct"].notna()].copy()
    if df_v.empty:
        return 0.0, pd.DataFrame(), pd.DataFrame()

    # Peso por fila según su línea
    df_v["_peso"] = df_v["Linea"].apply(
        lambda l: _PESOS_LINEA.get(_nm_linea(str(l)), _PESO_DEFAULT / len(_PESOS_LINEA))
    )

    # Promedio ponderado global
    denom = df_v["_peso"].sum()
    if denom == 0:
        return 0.0, pd.DataFrame(), pd.DataFrame()
    base_score = float((df_v["cumplimiento_pct"] * df_v["_peso"]).sum() / denom)

    # Ajustes por distribución de niveles
    n_total = len(df_v)
    n_sobre  = int((df_v["Nivel de cumplimiento"] == "Sobrecumplimiento").sum())
    n_peligro = int((df_v["Nivel de cumplimiento"] == "Peligro").sum())
    n_alerta  = int((df_v["Nivel de cumplimiento"] == "Alerta").sum())
    ajuste = (
        (n_sobre  / n_total) * _BONUS_SOBRE +
        (n_peligro / n_total) * _PEN_PELIGRO +
        (n_alerta  / n_total) * _PEN_ALERTA
    ) if n_total else 0.0

    isi = float(min(max(base_score + ajuste, 0.0), 100.0))

    # Por línea
    por_linea = (
        df_v.groupby("Linea", dropna=False)
        .agg(
            indicadores=("cumplimiento_pct", "count"),
            cumplimiento=("cumplimiento_pct", "mean"),
            peligro=("Nivel de cumplimiento", lambda x: (x == "Peligro").sum()),
            alerta=("Nivel de cumplimiento",  lambda x: (x == "Alerta").sum()),
        )
        .reset_index()
    )
    por_linea["cumplimiento"] = por_linea["cumplimiento"].round(1)

    # Por objetivo
    por_obj = (
        df_v.groupby(["Linea", "Objetivo"], dropna=False)
        .agg(
            indicadores=("cumplimiento_pct", "count"),
            cumplimiento=("cumplimiento_pct", "mean"),
            peligro=("Nivel de cumplimiento", lambda x: (x == "Peligro").sum()),
        )
        .reset_index()
    )
    por_obj["cumplimiento"] = por_obj["cumplimiento"].round(1)

    return isi, por_linea, por_obj


def _fig_gauge_isi(isi: float) -> go.Figure:
    """Gauge semicircular para el Índice de Salud Institucional."""
    if isi >= 95:
        color = "#28a745"
        label = "Excelente"
    elif isi >= 80:
        color = "#a8d08d"
        label = "Bueno"
    elif isi >= 65:
        color = "#ffc107"
        label = "En riesgo"
    else:
        color = "#dc3545"
        label = "Crítico"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=isi,
        number={"suffix": "/100", "font": {"size": 32, "color": "#0f385a"}},
        delta={"reference": 80, "increasing": {"color": "#28a745"}, "decreasing": {"color": "#dc3545"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#9ba8b7"},
            "bar": {"color": color, "thickness": 0.30},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "#dce6f2",
            "steps": [
                {"range": [0, 65],  "color": "#FFCDD2"},
                {"range": [65, 80], "color": "#FEF9E7"},
                {"range": [80, 95], "color": "#E8F5E9"},
                {"range": [95, 100], "color": "#DDEEFF"},
            ],
            "threshold": {"line": {"color": "#0f385a", "width": 4}, "thickness": 0.9, "value": 80},
        },
        title={"text": f"Índice de Salud Institucional<br><span style='font-size:0.85rem;color:{color}'>{label}</span>",
               "font": {"size": 15, "color": "#0f385a"}},
    ))
    fig.update_layout(
        height=300,
        margin=dict(t=60, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _option_gauge_isi(isi: float) -> dict:
    # colores y etiqueta coherentes con la implementación Plotly
    if isi >= 95:
        color = "#28a745"
        label = "Excelente"
    elif isi >= 80:
        color = "#a8d08d"
        label = "Bueno"
    elif isi >= 65:
        color = "#ffc107"
        label = "En riesgo"
    else:
        color = "#dc3545"
        label = "Crítico"

    option = {
        "series": [
            {
                "type": "gauge",
                "min": 0,
                "max": 100,
                "startAngle": 180,
                "endAngle": 0,
                "progress": {"show": True, "width": 18},
                "axisLine": {
                    "lineStyle": {
                        "width": 18,
                        "color": [
                            [0.65, "#FFCDD2"],
                            [0.8, "#FEF9E7"],
                            [0.95, "#E8F5E9"],
                            [1.0, "#DDEEFF"],
                        ],
                    }
                },
                "pointer": {"itemStyle": {"color": color}},
                "detail": {"valueAnimation": True, "formatter": "{value}/100", "fontSize": 18},
                "data": [{"value": float(isi), "name": label}],
                "title": {"fontSize": 14},
            }
        ]
    }
    return {"option": option, "height": 320}


def _fig_treemap_pdi(df: pd.DataFrame) -> go.Figure:
    """Treemap jerárquico: PDI → Línea → Objetivo → Indicador.

    Color por cumplimiento_pct; tamaño uniforme (1 por indicador).
    """
    req = {"Linea", "Objetivo", "Id", "cumplimiento_pct"}
    if not req.issubset(df.columns) or df.empty:
        return go.Figure()

    df_t = df.copy()
    df_t["Indicador_label"] = df_t.apply(
        lambda r: f"{r['Id']}: {str(r.get('Indicador',''))[:45]}", axis=1
    )
    df_t["cumplimiento_pct"] = pd.to_numeric(df_t["cumplimiento_pct"], errors="coerce").fillna(0)
    df_t["_size"] = 1

    # Etiqueta de texto con % para hover
    df_t["_label_hover"] = df_t["cumplimiento_pct"].apply(lambda v: f"{v:.1f}%")

    # Convertir a estructura anidada para ECharts
    # Root -> Linea -> Objetivo -> Indicador
    tree = {}
    for _, r in df_t.iterrows():
        linea = str(r.get('Linea') or 'Sin Línea')
        objetivo = str(r.get('Objetivo') or 'Sin objetivo')
        label = r.get('Indicador_label')
        val = float(r.get('cumplimiento_pct', 0))
        node = {'name': label, 'value': 1, 'cumplimiento': val, 'nivel': r.get('Nivel de cumplimiento', '')}

        tree.setdefault(linea, {})
        tree[linea].setdefault(objetivo, []).append(node)

    def _node_color(v):
        # Map cumplimiento pct (0-130) to color stops similar to Plotly scale
        try:
            pct = float(v)
        except Exception:
            pct = 0.0
        if pct < 65:
            return '#FFCDD2'
        if pct < 80:
            return '#FEF9E7'
        if pct < 100:
            return '#E8F5E9'
        return '#D0E4FF'

    data = []
    for linea, objetivos in tree.items():
        children_linea = []
        for obj, items in objetivos.items():
            children_obj = []
            for it in items:
                children_obj.append({
                    'name': it['name'],
                    'value': it['value'],
                    'itemStyle': {'color': _node_color(it['cumplimiento'])},
                    'label': {'show': False},
                })
            children_linea.append({'name': obj, 'children': children_obj})
        data.append({'name': linea, 'children': children_linea})

    option = {
        'title': {'text': 'Árbol de Objetivos PDI — Línea → Objetivo → Indicador', 'left': 'center'},
        'tooltip': {'formatter': '{b}'},
        'series': [{
            'type': 'treemap',
            'data': data,
            'label': {'show': True, 'formatter': '{b}'},
            'leafDepth': 2,
            'upperLabel': {'show': True, 'height': 30},
            'breadcrumb': {'show': True},
        }],
    }
    return option


def _default_corte(anios: list[int]) -> tuple[int, str]:
    if 2025 in anios:
        return 2025, "Diciembre"
    if anios:
        return anios[-1], "Diciembre"
    return _date.today().year, "Diciembre"


def render():
    st.title("CMI Estratégico")
    st.caption("Indicadores del Plan Estratégico (PDI) con cumplimiento de cierre y niveles institucionales.")

    # Inyectar paleta global (variables CSS)
    set_global_palette({
        'primary': '#0B5FFF', 'success': '#16A34A', 'alert': '#F59E0B',
        'danger': '#DC2626', 'bg': '#F5F7FA', 'panel': '#FFFFFF', 'text': '#0F1724'
    })

    cierres = load_cierres()
    if cierres.empty:
        st.error("No se encontró información de cierres en Resultados Consolidados.xlsx.")
        return

    anios = sorted(pd.to_numeric(cierres["Anio"], errors="coerce").dropna().astype(int).unique().tolist())
    if not anios:
        st.error("No hay años disponibles en consolidado de cierres.")
        return

    # Primary filter strip (visible)
    _anio_default, _corte_default = _default_corte(anios)
    f1, f2, f3 = st.columns([1,1,1])
    with f1:
        anio = st.selectbox("Año de corte", anios, index=anios.index(_anio_default), key="cmi_pdi_anio")
    with f2:
        corte = st.selectbox(
            "Corte semestral",
            list(CORTE_SEMESTRAL.keys()),
            index=list(CORTE_SEMESTRAL.keys()).index(_corte_default),
            key="cmi_pdi_corte",
        )
    with f3:
        if st.button("Limpiar filtros", key="cmi_pdi_clear"):
            for k in [
                "cmi_pdi_anio", "cmi_pdi_mes", "cmi_pdi_linea", "cmi_pdi_objetivo", "cmi_pdi_nombre",
                "_cmi_pdi_last_anio",
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
    mes = CORTE_SEMESTRAL[corte]

    # Secondary (advanced) filters inside expander
    with st.expander("🔎 Filtros avanzados", expanded=False):
        _ff1, _ff2, _ff3 = st.columns([1, 2, 2])
        with _ff1:
            linea_sel = st.selectbox("Línea estratégica", ["Todas"] + lineas, key="cmi_pdi_linea")
        with _ff2:
            objetivo_sel = st.selectbox("Objetivo estratégico", ["Todos"] + objetivos, key="cmi_pdi_objetivo")
        with _ff3:
            nombre_q = st.text_input("Buscar indicador", key="cmi_pdi_nombre", placeholder="Texto en nombre del indicador")

    df = preparar_pdi_con_cierre(int(anio), int(mes))
    if df.empty:
        st.warning("No hay indicadores PDI (flag=1) para el corte seleccionado.")
        return

    pdi_catalog = load_pdi_catalog()
    lineas = sorted(
        pdi_catalog["Linea"].dropna().astype(str).unique().tolist()
        if not pdi_catalog.empty else df["Linea"].dropna().astype(str).unique().tolist()
    )
    # Update objetivo list based on linea selection
    if 'linea_sel' in locals() and linea_sel != "Todas":
        obj_pool = pdi_catalog if linea_sel == "Todas" else pdi_catalog[pdi_catalog["Linea"] == linea_sel]
        objetivos = sorted(obj_pool["Objetivo"].dropna().astype(str).unique().tolist())
    else:
        obj_pool = pdi_catalog
        objetivos = sorted(pdi_catalog["Objetivo"].dropna().astype(str).unique().tolist()) if not pdi_catalog.empty else sorted(df["Objetivo"].dropna().astype(str).unique().tolist())

    # Apply secondary filters if set
    if 'linea_sel' in locals() and linea_sel != "Todas":
        df = df[df["Linea"] == linea_sel]
    if 'objetivo_sel' in locals() and objetivo_sel != "Todos":
        df = df[df["Objetivo"] == objetivo_sel]
    if 'nombre_q' in locals() and nombre_q.strip():
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

    # --- Render embebible Executive Summary (prototipo A) -----------------
    try:
        niveles_count = df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().to_dict()
        donut_data = [{"value": int(v), "name": str(k)} for k, v in niveles_count.items()]
        # Generate small sparklines (6 points) from historical cumplimiento if possible
        def _sparkline_from_df(d):
            try:
                if 'Fecha' in d.columns:
                    s = d.sort_values('Fecha')['cumplimiento_pct'].dropna().tolist()
                elif 'Anio' in d.columns:
                    s = d.sort_values(['Anio','Mes'] if 'Mes' in d.columns else ['Anio'])['cumplimiento_pct'].dropna().tolist()
                else:
                    s = d['cumplimiento_pct'].dropna().tolist()
                if not s:
                    return [round(promedio,1)] * 6
                # take last up to 6 points, pad if needed
                arr = [float(x) for x in s[-6:]]
                if len(arr) < 6:
                    arr = ([arr[0]] * (6 - len(arr))) + arr
                return arr
            except Exception:
                return [round(promedio,1)] * 6

        spark = _sparkline_from_df(df)

        exec_data = {
            "kpis": [
                {"title": "Indicadores PDI", "value": total, "meta": f"Reportados: {con_dato}", "trend": "", "sparkline": spark},
                {"title": "Promedio cumplimiento", "value": f"{promedio:.1f}%", "meta": "Último periodo", "trend": "", "sparkline": spark},
                {"title": "Salud institucional", "value": f"{isi:.1f}/100", "meta": "Umbral 80", "trend": "", "sparkline": spark},
            ],
            "donut": donut_data,
            "insight": f"Top linea: {top_nivel}. {total} indicadores analizados.",
        }
        render_exec_summary(exec_data, height=380)
    except Exception as _e:
        st.warning("No se pudo renderizar Executive Summary embebible: " + str(_e))

    # ── Índice de Salud Institucional ──────────────────────────────────────
    isi, por_linea, por_obj = _calcular_isi(df)

    # Mostrar alerta si ISI crítico y un panel narrativo con insight
    try:
        if isi < 65:
            render_alert_strip(f"ALERTA: Índice de Salud Institucional {isi:.1f}/100 — nivel Crítico. Revisar líneas con mayor riesgo.", level='danger')
        render_narrative_panel("Insight rápido", f"ISI: {isi:.1f}/100 · Indicadores analizados: {total} · Promedio cumplimiento: {promedio:.1f}%", collapsed=False)
    except Exception:
        pass

    from streamlit_app.components.renderers import kpi_card
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        try:
            kpi_card("Indicadores PDI", total, sparkline=spark)
        except Exception:
            st.metric("Indicadores PDI", total)
    with k2:
        try:
            kpi_card("Con cumplimiento", con_dato, sparkline=spark)
        except Exception:
            st.metric("Con cumplimiento", con_dato)
    with k3:
        try:
            kpi_card("Promedio cumplimiento", f"{promedio:.1f}%", sparkline=spark)
        except Exception:
            st.metric("Promedio cumplimiento", f"{promedio:.1f}%")
    with k4:
        try:
            kpi_card("Nivel predominante", top_nivel, sparkline=spark)
        except Exception:
            st.metric("Nivel predominante", top_nivel)
    with k5:
        try:
            kpi_card("🏥 Salud institucional", f"{isi:.1f}/100", delta=f"{isi - 80:+.1f} vs umbral 80", sparkline=spark)
        except Exception:
            k5.metric(
                "🏥 Salud institucional",
                f"{isi:.1f}/100",
                delta=f"{isi - 80:+.1f} vs umbral 80",
                delta_color="normal",
            )

    st.caption(f"Corte seleccionado: {corte} {anio}")
    st.caption(
        f"Catálogo PDI: {n_lineas_cat} líneas y {n_obj_cat} objetivos. "
        f"Con indicadores Plan Estratégico=1 en corte: {n_lineas_vis} líneas y {n_obj_vis} objetivos."
    )

    # ── Panel ISI + tabla por línea ────────────────────────────────────────
    isi_c1, isi_c2 = st.columns([1, 2])
    with isi_c1:
        try:
            from streamlit_app.components.renderers import render_echarts
            opt = _option_gauge_isi(isi)
            if opt and opt.get('option'):
                render_echarts(opt['option'], height=opt.get('height', 320))
            else:
                st.plotly_chart(_fig_gauge_isi(isi), use_container_width=True, key="cmi_isi_gauge")
        except Exception:
            st.plotly_chart(_fig_gauge_isi(isi), use_container_width=True, key="cmi_isi_gauge")
    with isi_c2:
        if not por_linea.empty:
            st.markdown("**Salud por línea estratégica**")
            _pl = por_linea.copy()
            _pl.columns = ["Línea", "Indicadores", "Cumpl. promedio (%)", "En Peligro", "En Alerta"]
            _pl["Cumpl. promedio (%)"] = _pl["Cumpl. promedio (%)"].round(1)
            st.dataframe(_pl, use_container_width=True, hide_index=True, height=240)

    if not por_obj.empty:
        with st.expander("Detalle por objetivo estratégico", expanded=False):
            _po = por_obj.copy()
            _po.columns = ["Línea", "Objetivo", "Indicadores", "Cumpl. promedio (%)", "En Peligro"]
            _po["Cumpl. promedio (%)"] = _po["Cumpl. promedio (%)"].round(1)
            _po = _po.sort_values(["Línea", "Cumpl. promedio (%)"])
            st.dataframe(_po, use_container_width=True, hide_index=True, height=320)

    st.markdown("---")

    c1, c2 = st.columns([1, 1])
    with c1:
        by_linea = (
            df.groupby("Linea", dropna=False)["cumplimiento_pct"]
            .mean().fillna(0).reset_index().sort_values("cumplimiento_pct", ascending=True)
        )
        by_linea["Linea"] = by_linea["Linea"].astype(str)
        # Prepare ECharts option for horizontal bar
        data_bar = [{"name": r["Linea"], "value": round(float(r["cumplimiento_pct"]),1)} for _, r in by_linea.iterrows()]
        colors_bar = [ _linea_color(r["Linea"]) for _, r in by_linea.iterrows() ]
        option_bar = {
            "title": {"text": "Cumplimiento promedio por línea estratégica", "left": "center"},
            "grid": {"left": "8%", "right": "8%", "bottom": "6%", "top": "12%"},
            "xAxis": {"type": "value", "name": "Cumplimiento (%)"},
            "yAxis": {"type": "category", "data": [d["name"] for d in data_bar]},
            "series": [{"type": "bar", "data": [d["value"] for d in data_bar], "label": {"show": True, "position": "right", "formatter": "{c}%"}}],
            "color": colors_bar,
        }
        render_echarts(option_bar, height=320)

    with c2:
        niveles = df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
        niveles.columns = ["Nivel", "Cantidad"]
        data_pie = [{"name": r["Nivel"], "value": int(r["Cantidad"])} for _, r in niveles.iterrows()]
        colors_pie = [NIVEL_COLOR_EXT.get(d["name"], "#9AA6B2") for d in data_pie]
        option_pie = {
            "title": {"text": "Distribución por nivel", "left": "center"},
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "horizontal", "bottom": 0},
            "series": [{"type": "pie", "radius": ["45%", "65%"], "data": data_pie, "label": {"show": False}}],
            "color": colors_pie,
        }
        render_echarts(option_pie, height=320)

    # Treemap PDI — usar ECharts para mejor interactividad
    try:
        option_tm = _fig_treemap_pdi(df)
        if option_tm:
            render_echarts(option_tm, height=520)
    except Exception:
        pass

    st.markdown("### Indicadores PDI")
    _cols_pdi = ["Id", "Indicador", "Linea", "Objetivo", "cumplimiento_pct", "Nivel de cumplimiento"]
    if "Meta" in df.columns:
        _cols_pdi.append("Meta")
    if "Ejecucion" in df.columns:
        _cols_pdi.append("Ejecucion")
    if "Sentido" in df.columns:
        _cols_pdi.append("Sentido")
    _cols_pdi += ["Anio", "Mes", "Fecha"]
    tabla = df[[c for c in _cols_pdi if c in df.columns]].copy()
    tabla = tabla.rename(columns={
        "cumplimiento_pct": "Cumplimiento (%)",
        "Nivel de cumplimiento": "Nivel",
        "Anio": "Año cierre",
        "Mes": "Mes cierre",
        "Meta": "Meta",
        "Ejecucion": "Ejecución",
    })
    tabla["Cumplimiento (%)"] = pd.to_numeric(tabla["Cumplimiento (%)"], errors="coerce").round(1)
    if "Meta" in tabla.columns:
        tabla["Meta"] = pd.to_numeric(tabla["Meta"], errors="coerce").round(2)
    if "Ejecución" in tabla.columns:
        tabla["Ejecución"] = pd.to_numeric(tabla["Ejecución"], errors="coerce").round(2)
    tabla = tabla.sort_values(["Linea", "Objetivo", "Id"] if all(c in tabla.columns for c in ["Linea", "Objetivo"]) else ["Id"], na_position="last")

    # Color de fondo por Nivel en columna Nivel
    _NIVEL_BG_CMI = {
        "Peligro": "#FFCDD2", "Alerta": "#FEF3D0", "Cumplimiento": "#E8F5E9",
        "Sobrecumplimiento": "#D0E4FF", "No aplica": "#ECEFF1", "Pendiente de reporte": "#F5F5F5",
    }
    _NIVEL_ICONS_CMI = {
        "Peligro": "🔴", "Alerta": "🟡", "Cumplimiento": "🟢",
        "Sobrecumplimiento": "🔵", "No aplica": "⚫", "Pendiente de reporte": "⚪",
    }
    if "Nivel" in tabla.columns:
        tabla["Nivel"] = tabla["Nivel"].apply(
            lambda n: f'{_NIVEL_ICONS_CMI.get(str(n), "")} {n}' if pd.notna(n) else n
        )
    if "Linea" in tabla.columns:
        tabla["Color Línea"] = tabla["Linea"].apply(lambda l: _linea_color(str(l or "")))

    _cfg_pdi = {
        "Id":        st.column_config.TextColumn("ID",          width="small"),
        "Indicador": st.column_config.TextColumn("Indicador",   width="large"),
        "Linea":     st.column_config.TextColumn("Línea",       width="medium"),
        "Objetivo":  st.column_config.TextColumn("Objetivo",    width="large"),
        "Nivel":     st.column_config.TextColumn("Nivel",       width="medium"),
        "Cumplimiento (%)": st.column_config.NumberColumn("Cumplimiento %", format="%.1f", width="small"),
        "Meta":      st.column_config.NumberColumn("Meta",      format="%.2f", width="small"),
        "Ejecución": st.column_config.NumberColumn("Ejecución", format="%.2f", width="small"),
        "Sentido":   st.column_config.TextColumn("Sentido",     width="small"),
        "Año cierre": st.column_config.NumberColumn("Año",      format="%d",   width="small"),
        "Mes cierre": st.column_config.NumberColumn("Mes",      format="%d",   width="small"),
        "Fecha":     st.column_config.DatetimeColumn("Fecha",   width="small"),
    }
    # Renderizar indicadores PDI por Línea: título con color y tarjetas por Objetivo
    def _render_indicator_table(df_obj: pd.DataFrame) -> str:
        """Retorna HTML de una tabla compacta con columnas Indicador, Meta, Ejecución, Cumplimiento."""
        cols = [c for c in ["Indicador", "Meta", "Ejecución", "Cumplimiento (%)"] if c in df_obj.columns]
        if df_obj.empty:
            return "<div style='padding:8px'>No hay indicadores para este objetivo.</div>"
        html = ["<table style='width:100%;border-collapse:collapse;font-size:0.9rem'>"]
        # header
        html.append("<tr style='background:#e9f7fb;color:#033;'><th style='padding:8px;border:1px solid #d0e9ef;text-align:left'>Indicador</th>")
        for c in cols[1:]:
            html.append(f"<th style='padding:8px;border:1px solid #d0e9ef;text-align:center'>{c}</th>")
        html.append("</tr>")
        # rows
        for _, r in df_obj.iterrows():
            html.append("<tr>")
            html.append(f"<td style='padding:8px;border:1px solid #eef7fb'>{_escape(str(r.get('Indicador','')))}</td>")
            for c in cols[1:]:
                val = r.get(c, "")
                display = f"{val}" if pd.notna(val) else ""
                align = "center"
                html.append(f"<td style='padding:8px;border:1px solid #eef7fb;text-align:{align}'>{display}</td>")
            html.append("</tr>")
        html.append("</table>")
        return "".join(html)

    # Ordenar líneas según catálogo (asegurar las seis líneas ordenadas)
    ordered_lineas = [l for l in LINEA_COLORS.keys() if l in tabla['Linea'].unique()] + [l for l in tabla['Linea'].unique() if l not in LINEA_COLORS.keys()]
    from html import escape as _escape

    # Opción: mostrar tabla completa paginada
    from streamlit_app.components.renderers import render_table_paginated
    if st.checkbox("Mostrar tabla completa (paginada)", value=False, key="show_full_table"):
        render_table_paginated(tabla, page_size=20, key="tabla_pdi_full")

    # Ordenar líneas según catálogo (asegurar las seis líneas ordenadas)
    ordered_lineas = [l for l in LINEA_COLORS.keys() if l in tabla['Linea'].unique()] + [l for l in tabla['Linea'].unique() if l not in LINEA_COLORS.keys()]
    from html import escape as _escape

    for linea in ordered_lineas:
        color = LINEA_COLORS.get(linea, _linea_color(linea))
        st.markdown(f"<div style='background:{color};padding:14px;border-radius:6px;margin-top:12px;margin-bottom:8px'><h3 style='color:#ffffff;margin:0;padding:0'>{_escape(linea)}</h3></div>", unsafe_allow_html=True)
        df_line = tabla[tabla['Linea'] == linea].copy()
        if df_line.empty:
            st.info(f"No hay indicadores PDI para la línea {linea} en el corte seleccionado.")
            continue
        # Agrupar por Objetivo y renderizar tarjetas en dos columnas
        objetivos = df_line['Objetivo'].fillna('Sin objetivo').unique().tolist()
        cols_iter = iter(objetivos)
        while True:
            try:
                o1 = next(cols_iter)
            except StopIteration:
                break
            o2 = None
            try:
                o2 = next(cols_iter)
            except StopIteration:
                o2 = None
            c1, c2 = st.columns([1,1])
            with c1:
                df_o1 = df_line[df_line['Objetivo'] == o1]
                st.markdown(f"<div style='background:#f2fbfb;border-radius:6px;padding:8px'><strong>{_escape(str(o1))}</strong></div>", unsafe_allow_html=True)
                st.markdown(_render_indicator_table(df_o1), unsafe_allow_html=True)
            with c2:
                if o2:
                    df_o2 = df_line[df_line['Objetivo'] == o2]
                    st.markdown(f"<div style='background:#f2fbfb;border-radius:6px;padding:8px'><strong>{_escape(str(o2))}</strong></div>", unsafe_allow_html=True)
                    st.markdown(_render_indicator_table(df_o2), unsafe_allow_html=True)
        # separación entre líneas
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Acciones de mejora asociadas (integración de acciones_table) ─────
    st.markdown("---")
    st.markdown("### 📋 Acciones de Mejora asociadas")
    st.caption("Acciones registradas en acciones_mejora.xlsx vinculadas al corte actual.")

    df_acc = cargar_acciones_mejora()
    if df_acc.empty:
        st.info("No hay datos de acciones de mejora disponibles.")
    else:
        # buscar columna ID indicador
        id_col_acc = None
        for cand in ("ID_INDICADOR", "Id", "ID", "INDICADOR_ID", "id_indicador"):
            if cand in df_acc.columns:
                id_col_acc = cand
                break

        # si no hay columna ID, mostrar todas las acciones concentradas por línea si existe
        if id_col_acc is None:
            # si existe columna 'Linea' o 'Línea', filtrar por linea_sel
            df_acc_v = df_acc.copy()
            if 'linea_sel' in locals() and linea_sel != 'Todas' and 'Linea' in df_acc_v.columns:
                df_acc_v = df_acc_v[df_acc_v['Linea'] == linea_sel]
            actions_table(df_acc_v)
        else:
            ids_visible = set(tabla['Id'].astype(str).str.strip().unique())
            df_acc_v = df_acc.copy()
            df_acc_v['_id_norm'] = df_acc_v[id_col_acc].apply(lambda x: str(int(float(x))) if str(x).replace('.', '').isdigit() else str(x).strip())
            df_acc_cna = df_acc_v[df_acc_v['_id_norm'].isin(ids_visible)].copy()
            if df_acc_cna.empty:
                st.info("No se encontraron acciones vinculadas a los indicadores del corte actual.")
            else:
                actions_table(df_acc_cna)

