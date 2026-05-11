"""
Accreditation and gap management dashboard (Level 2).

Refactored PHASE 2 WEEK 4: Extracted config and utility functions.
"""

import os
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

# Importes desde root
try:
    from core.config import NIVEL_COLOR, NIVEL_BG, UMBRAL_PELIGRO, UMBRAL_ALERTA
    from services.data_loader import cargar_dataset, cargar_acciones_mejora
except (ImportError, ModuleNotFoundError):
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.config import NIVEL_COLOR, NIVEL_BG, UMBRAL_PELIGRO, UMBRAL_ALERTA
    from services.data_loader import cargar_dataset, cargar_acciones_mejora

# Importes desde streamlit_app
try:
    from ..components.filter_panel import render_filter_panel
    from ..utils.formatting import formatear_meta_ejecucion_df
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from streamlit_app.components.filter_panel import render_filter_panel
    from utils.formatting import formatear_meta_ejecucion_df

# Import refactored utilities
from .pdi_config import FILTER_DEFINITIONS, MATRIX_COLUMNS, CNA_SHEET
from .pdi_utils import (
    preparar_datos_acciones,
    aplicar_filtros,
    enriquecer_datos_cna,
    extraer_columna_cumplimiento,
    clasificar_estado,
)

# Re-export for backward compatibility with tests
_clasificar_estado = clasificar_estado


def render():
    """Main render function for PDI accreditation page."""
    st.title("Gestión y Acreditación (Nivel 2)")
    st.caption("Panel de cumplimiento, brechas y matriz de acreditación.")

    # --- Filtros ---
    sel = render_filter_panel(
        filters=FILTER_DEFINITIONS,
        title="Filtros",
        key_prefix="pdi",
        n_cols=3,
        show_reset=True,
        reset_keys=["pdi_estado", "pdi_macro", "pdi_horizonte"],
    )

    activos = []
    if sel.get("estado", "Todos") != "Todos":
        activos.append(f"Estado: {sel['estado']}")
    if sel.get("macro", "Todos") != "Todos":
        activos.append(f"Macrolinea: {sel['macro']}")
    if sel.get("horizonte"):
        activos.append(f"Horizonte: {sel['horizonte']}")
    if activos:
        st.caption("Filtros activos: " + " · ".join(activos))

    # --- Cargar datos reales ---
    df = cargar_dataset()
    if df.empty:
        st.warning("No hay datos disponibles para la matriz de acreditación.")
        return

    # --- Filtrado y normalización ---
    df = df[df["Clasificacion"].str.contains("acredit", case=False, na=False)]
    df = df.copy()

    # Cargar catálogo CNA
    cna_path = os.path.join(os.path.dirname(__file__), "../../data/db/Indicadores por CMI.xlsx")
    try:
        df_cna = pd.read_excel(cna_path, sheet_name=CNA_SHEET)
    except Exception:
        df_cna = pd.DataFrame()

    # Enrich with CNA metadata
    df = enriquecer_datos_cna(df, df_cna)

    # Extract and prepare compliance data
    try:
        col_cumpl, cumpl_series = extraer_columna_cumplimiento(df)
        df["cumplimiento_pct"] = cumpl_series
    except ValueError as e:
        st.error(str(e))
        return

    # Prepare data with Estado classification and gaps
    df = preparar_datos_acciones(df)

    # Apply filters
    df = aplicar_filtros(df, sel)

    # --- KPIs Scorecard ---
    k1, k2 = st.columns(2)
    k1.metric(
        "Cumplimiento promedio (%)",
        f"{df['cumplimiento_pct'].mean():.1f}%" if not df.empty else "-",
    )
    k2.metric("Brecha promedio (pp)", f"{df['brecha'].mean():.1f}" if not df.empty else "-")

    # --- Árbol de Objetivos (Treemap drill-down) ---
    st.markdown("#### Árbol de Objetivos (drill-down)")
    if not df.empty and all(c in df.columns for c in ["Macrolinea", "Objetivo", "Indicador"]):
        df_tm = df.copy()
        df_tm["_size"] = 1
        df_tm["Indicador_label"] = df_tm.apply(
            lambda r: f"{r['Id']}: {str(r.get('Indicador',''))[:40]}", axis=1
        )
        fig_tm = px.treemap(
            df_tm,
            path=["Macrolinea", "Objetivo", "Indicador_label"],
            values="_size",
            color="cumplimiento_pct",
            color_continuous_scale=[
                NIVEL_COLOR["Peligro"],
                NIVEL_COLOR["Alerta"],
                NIVEL_COLOR["Cumplimiento"],
                NIVEL_COLOR["Sobrecumplimiento"],
            ],
            range_color=[0, 130],
            title="Árbol de Objetivos: Macrolinea → Objetivo → Indicador",
        )
        fig_tm.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10, l=10, r=10), height=420
        )
        try:
            from ..components.renderers import render_echarts

            tree_data = []
            for macro, gmacro in df_tm.groupby("Macrolinea"):
                macro_children = []
                for obj, gobj in gmacro.groupby("Objetivo"):
                    obj_children = []
                    for _, r in gobj.iterrows():
                        obj_children.append(
                            {"name": r["Indicador_label"], "value": int(r["_size"])}
                        )
                    macro_children.append({"name": str(obj), "children": obj_children})
                tree_data.append({"name": str(macro), "children": macro_children})
            option = {"series": [{"type": "treemap", "data": tree_data}]}
            render_echarts(option, height=420)
        except Exception:
            st.plotly_chart(fig_tm, use_container_width=True)
    else:
        st.info("No hay datos suficientes para el árbol de objetivos.")

    # --- Comparativa vs Benchmark (mock) ---
    st.markdown("#### Comparativa vs Benchmark (mock)")
    if "Proceso" in df.columns:
        df_bench = (
            df.groupby("Proceso", dropna=False)
            .agg(cumplimiento=("cumplimiento_pct", "mean"))
            .reset_index()
        )
        df_bench["benchmark"] = df_bench["cumplimiento"] - 5
        fig_bench = px.bar(
            df_bench.melt(
                id_vars="Proceso",
                value_vars=["cumplimiento", "benchmark"],
                var_name="Serie",
                value_name="% Cumplimiento",
            ),
            x="Proceso",
            y="% Cumplimiento",
            color="Serie",
            barmode="group",
            color_discrete_map={
                "cumplimiento": NIVEL_COLOR["Cumplimiento"],
                "benchmark": NIVEL_COLOR["Alerta"],
            },
            title="Cumplimiento propio vs benchmark (simulado)",
        )
        try:
            from ..components.renderers import render_echarts

            df_m = df_bench.melt(
                id_vars="Proceso",
                value_vars=["cumplimiento", "benchmark"],
                var_name="Serie",
                value_name="Valor",
            )
            procs = df_m["Proceso"].astype(str).unique().tolist()
            series = []
            for serie in df_m["Serie"].unique():
                vals = [
                    float(
                        df_m[(df_m["Proceso"] == p) & (df_m["Serie"] == serie)]["Valor"].sum() or 0
                    )
                    for p in procs
                ]
                series.append({"name": serie, "type": "bar", "data": vals})
            option = {
                "tooltip": {"trigger": "axis"},
                "legend": {"bottom": 0},
                "xAxis": {"type": "category", "data": procs},
                "yAxis": {"type": "value"},
                "series": series,
            }
            render_echarts(option, height=340)
        except Exception:
            st.plotly_chart(fig_bench, use_container_width=True)
    else:
        st.info("No hay datos de proceso para comparar benchmark.")

    # --- Evolución de brechas (línea de tiempo) ---
    st.markdown("#### Evolución de brechas promedio por periodo")
    if "Periodo" in df.columns and "Proceso" in df.columns:
        df_evo = (
            df.groupby(["Periodo", "Proceso"], dropna=False)
            .agg(brecha=("brecha", "mean"))
            .reset_index()
        )
        fig_evo = px.line(
            df_evo,
            x="Periodo",
            y="brecha",
            color="Proceso",
            markers=True,
            title="Brecha promedio por proceso a lo largo del tiempo",
        )
        try:
            from ..components.renderers import render_echarts

            periods = sorted(df_evo["Periodo"].astype(str).unique().tolist())
            procs = sorted(df_evo["Proceso"].astype(str).unique().tolist())
            series = []
            for p in procs:
                vals = []
                for per in periods:
                    v = df_evo[(df_evo["Periodo"].astype(str) == per) & (df_evo["Proceso"] == p)][
                        "brecha"
                    ]
                    vals.append(float(v.values[0]) if not v.empty else None)
                series.append({"name": p, "type": "line", "data": vals})
            option = {
                "tooltip": {"trigger": "axis"},
                "legend": {"bottom": 0},
                "xAxis": {"type": "category", "data": periods},
                "yAxis": {"type": "value"},
                "series": series,
            }
            render_echarts(option, height=340)
        except Exception:
            st.plotly_chart(fig_evo, use_container_width=True)
    else:
        st.info("No hay datos de periodo/proceso para evolución de brechas.")

    st.markdown("---")

    # --- Matriz de acreditación ---
    st.markdown("#### Matriz de acreditación")
    cols = [c for c in MATRIX_COLUMNS if c in df.columns]
    if cols and not df.empty:
        tabla = df[cols].copy()
        tabla = tabla.rename(
            columns={
                "cumplimiento_pct": "% Cumplimiento",
                "Meta": "Meta",
                "Ejecucion": "Ejecución",
                "Linea": "Macrolinea",
            }
        )
        tabla = formatear_meta_ejecucion_df(tabla, meta_col="Meta", ejec_col="Ejecución")
        st.dataframe(tabla, use_container_width=True, hide_index=True, height=420)
    else:
        st.info("No hay columnas disponibles para mostrar la matriz.")
