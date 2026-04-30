from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.services.data_service import DataService
from services.cmi_filters import filter_df_for_cmi_procesos
from core.proceso_types import TIPOS_PROCESO, get_tipo_color

MESES_OPCIONES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

MES_MAP = {m.upper(): i + 1 for i, m in enumerate(MESES_OPCIONES)}


def _mes_to_num(value: object) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        try:
            v = int(value)
            return float(v) if 1 <= v <= 12 else None
        except Exception:
            return None

    txt = str(value).strip()
    if not txt:
        return None

    if txt.isdigit():
        v = int(txt)
        return float(v) if 1 <= v <= 12 else None

    txt_norm = txt.upper()
    return float(MES_MAP.get(txt_norm)) if txt_norm in MES_MAP else None


def _get_prev_month_for_year(tracking_df: pd.DataFrame, year: int) -> int | None:
    if tracking_df.empty or "Anio" not in tracking_df.columns:
        return None
    subset = tracking_df[tracking_df["Anio"] == year].copy()
    if subset.empty:
        return None
    if "Mes_num" in subset.columns:
        months = pd.to_numeric(subset["Mes_num"], errors="coerce")
    elif "Mes" in subset.columns:
        months = subset["Mes"].apply(_mes_to_num)
    else:
        return None
    months = pd.to_numeric(months, errors="coerce").dropna().astype(int)
    return int(months.max()) if not months.empty else None


def _prepare_resumen_df(df: pd.DataFrame, map_df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return out

    if not map_df.empty and "Subproceso" in out.columns and "Tipo de proceso" in map_df.columns:
        merge_cols = [c for c in ["Subproceso", "Proceso", "Tipo de proceso"] if c in map_df.columns]
        out = out.merge(map_df[merge_cols].drop_duplicates(), on="Subproceso", how="left")
    if "Tipo de proceso" in out.columns:
        out["Tipo de proceso"] = out["Tipo de proceso"].astype(str).str.strip()
        out = out[out["Tipo de proceso"].notna()].copy()
    return out


def render() -> None:
    st.title("CMI por Procesos")

    ds = DataService()
    tracking_df = ds.get_tracking_data()
    map_df = ds.get_process_map()

    if tracking_df.empty:
        st.warning(
            "No se encontró data de seguimiento en data/output/Resultados Consolidados.xlsx (Consolidado Semestral)."
        )
        return
    if map_df.empty:
        st.warning("No se encontró el mapeo de procesos en data/raw/Subproceso-Proceso-Area.xlsx.")
        return

    years = (
        sorted(
            [
                int(y)
                for y in pd.to_numeric(tracking_df["Anio"], errors="coerce").dropna().unique().tolist()
            ]
        )
        if "Anio" in tracking_df.columns
        else []
    )
    default_month_num = _get_prev_month_for_year(tracking_df, max(years) if years else 2025) or 12
    default_month = MESES_OPCIONES[default_month_num - 1]

    st.markdown("#### Filtros")
    c1, c2 = st.columns(2)
    with c1:
        default_year = 2025 if 2025 in years else (years[-1] if years else None)
        default_year_idx = years.index(default_year) if default_year in years else 0
        anio = st.selectbox("Año", options=years, index=default_year_idx if years else None)
    with c2:
        mes = st.selectbox("Mes", options=MESES_OPCIONES, index=MESES_OPCIONES.index(default_month))

    month_num = MESES_OPCIONES.index(mes) + 1 if mes in MESES_OPCIONES else default_month_num

    cmi_global = tracking_df[tracking_df["Anio"] == int(anio)].copy()
    cmi_global = cmi_global[cmi_global["Mes"].apply(_mes_to_num) == float(month_num)].copy()
    cmi_global = filter_df_for_cmi_procesos(cmi_global, id_column="Id")
    cmi_global = _prepare_resumen_df(cmi_global, map_df)

    base_year = int(anio) - 1
    cmi_base = pd.DataFrame()
    if base_year in years:
        cmi_base = tracking_df[tracking_df["Anio"] == int(base_year)].copy()
        cmi_base = cmi_base[cmi_base["Mes"].apply(_mes_to_num) == float(month_num)].copy()
        cmi_base = filter_df_for_cmi_procesos(cmi_base, id_column="Id")
        cmi_base = _prepare_resumen_df(cmi_base, map_df)

    st.caption(
        f"Fuente: Consolidado Semestral · Resultados Consolidados.xlsx — Corte: {mes} {anio}."
    )

    if cmi_global.empty:
        st.warning("No hay indicadores de CMI por Procesos para el corte seleccionado.")
        return

    pct_col = "cumplimiento_pct" if "cumplimiento_pct" in cmi_global.columns else "Cumplimiento_pct"
    proc_col = "Proceso" if "Proceso" in cmi_global.columns else "Subproceso_final" if "Subproceso_final" in cmi_global.columns else "Subproceso"

    proc_curr = (
        cmi_global.groupby(proc_col, dropna=False)
        .agg(actual=(pct_col, "mean"), indicadores=("Indicador", "count"))
        .reset_index()
    )
    proc_base = pd.DataFrame()
    if not cmi_base.empty:
        _base_pct_col = "cumplimiento_pct" if "cumplimiento_pct" in cmi_base.columns else "Cumplimiento_pct"
        proc_base = (
            cmi_base.groupby(proc_col, dropna=False)
            .agg(base_2024=(_base_pct_col, "mean"))
            .reset_index()
        )

    proc_comp = proc_curr.merge(proc_base, on=proc_col, how="left") if not proc_base.empty else proc_curr.copy()
    proc_comp["delta_2024"] = proc_comp["actual"] - pd.to_numeric(proc_comp.get("base_2024", pd.Series(dtype="float64")), errors="coerce")
    proc_comp = proc_comp.sort_values("actual", ascending=False).head(10)

    avg_delta = proc_comp["delta_2024"].mean() if not proc_comp.empty else pd.NA
    best_delta = proc_comp["delta_2024"].max() if not proc_comp.empty else pd.NA
    worst_delta = proc_comp["delta_2024"].min() if not proc_comp.empty else pd.NA

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Variación media", f"{avg_delta:.1f}%" if pd.notna(avg_delta) else "N/A")
    col_b.metric("Mejor variación", f"{best_delta:.1f}%" if pd.notna(best_delta) else "N/A")
    col_c.metric("Peor variación", f"{worst_delta:.1f}%" if pd.notna(worst_delta) else "N/A")

    fig_bar = go.Figure()
    fig_bar.add_trace(
        go.Bar(
            name=f"Cumplimiento {anio}",
            x=proc_comp[proc_col],
            y=proc_comp["actual"],
            marker_color="#1E4C86",
        )
    )
    if "base_2024" in proc_comp.columns and proc_comp["base_2024"].notna().any():
        fig_bar.add_trace(
            go.Bar(
                name=f"Cumplimiento {base_year}",
                x=proc_comp[proc_col],
                y=proc_comp["base_2024"],
                marker_color="#9AB7D5",
            )
        )
    fig_bar.update_layout(
        barmode="group",
        height=380,
        margin=dict(t=20, b=120),
        xaxis_tickangle=-25,
        xaxis_title=proc_col,
        yaxis_title="Cumplimiento promedio (%)",
        legend_title_text="Comparación histórica",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    proc_table = proc_comp[[proc_col, "actual", "base_2024", "delta_2024"]].copy()
    proc_table = proc_table.rename(
        columns={
            proc_col: "Proceso",
            "actual": f"Cumplimiento {anio}",
            "base_2024": f"Cumplimiento {base_year}",
            "delta_2024": "Delta",
        }
    )
    for col in [f"Cumplimiento {anio}", f"Cumplimiento {base_year}", "Delta"]:
        if col in proc_table.columns:
            proc_table[col] = pd.to_numeric(proc_table[col], errors="coerce").round(1)

    st.markdown("#### Tabla de procesos comparativa")
    st.dataframe(proc_table, use_container_width=True, hide_index=True)
