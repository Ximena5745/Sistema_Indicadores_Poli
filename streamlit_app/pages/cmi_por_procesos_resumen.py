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
        merge_df = map_df[merge_cols].drop_duplicates(subset=["Subproceso"]) if "Subproceso" in merge_cols else map_df[merge_cols]
        out = out.merge(merge_df, on="Subproceso", how="left", suffixes=("", "_map"))

        if "Proceso" not in out.columns or out["Proceso"].isna().all():
            if "Proceso_map" in out.columns:
                out["Proceso"] = out["Proceso_map"]

        if "Tipo de proceso" not in out.columns or out["Tipo de proceso"].isna().all():
            if "Tipo de proceso_map" in out.columns:
                out["Tipo de proceso"] = out["Tipo de proceso_map"]

        for drop_col in ["Proceso_map", "Tipo de proceso_map"]:
            if drop_col in out.columns:
                out = out.drop(columns=[drop_col])

    if "Tipo de proceso" in out.columns:
        out["Tipo de proceso"] = out["Tipo de proceso"].astype(str).str.strip()
        out = out[out["Tipo de proceso"].notna()].copy()
    return out


def _compliance_color(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "#9E9E9E"
    try:
        feem = float(value)
    except Exception:
        return "#9E9E9E"
    if feem >= 1.05:
        return "#1B5E20"
    if feem >= 1.0:
        return "#2E7D32"
    if feem >= 0.8:
        return "#F59E0B"
    return "#C62828"


def _format_pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return str(value)


def _build_unit_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    group_cols = [c for c in ["Unidad", "Proceso"] if c in df.columns]
    if not group_cols:
        group_cols = ["Proceso"] if "Proceso" in df.columns else ["Subproceso"]
    summary = df.groupby(group_cols, dropna=False).agg(
        indicadores=("Indicador", "nunique"),
        cumplimiento=("cumplimiento_pct", "mean"),
    ).reset_index()
    summary["cumplimiento"] = pd.to_numeric(summary["cumplimiento"], errors="coerce")
    summary["cumplimiento"] = summary["cumplimiento"].round(3)
    return summary


def _build_frequency_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    group_cols = [c for c in ["Periodicidad", "Mes"] if c in df.columns]
    if not group_cols:
        return pd.DataFrame()
    summary = df.groupby(group_cols, dropna=False).agg(
        indicadores=("Indicador", "nunique"),
        cumplimiento=("cumplimiento_pct", "mean"),
    ).reset_index()
    summary["cumplimiento"] = pd.to_numeric(summary["cumplimiento"], errors="coerce").round(3)
    return summary


def _build_classification_summary(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["Clasificacion", "Tipo de proceso"] if c in df.columns]
    if not cols:
        return pd.DataFrame()
    summary = df.groupby(cols, dropna=False).agg(
        indicadores=("Indicador", "nunique"),
        cumplimiento=("cumplimiento_pct", "mean"),
    ).reset_index()
    summary["cumplimiento"] = pd.to_numeric(summary["cumplimiento"], errors="coerce").round(3)
    return summary


def _build_consolidated_columns(df: pd.DataFrame) -> list[str]:
    return [
        c
        for c in [
            "Proceso",
            "Subproceso",
            "Subproceso_final",
            "Indicador",
            "Clasificacion",
            "Periodicidad",
            "Mes",
            "cumplimiento_pct",
            "Meta",
            "Ejecucion",
            "Tipo de proceso",
            "Unidad",
        ]
        if c in df.columns
    ]


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

    def _ensure_cumplimiento_pct(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        if "cumplimiento_pct" in df.columns or "Cumplimiento_pct" in df.columns:
            return df
        df = df.copy()
        if "Cumplimiento" in df.columns:
            df["cumplimiento_pct"] = pd.to_numeric(df["Cumplimiento"], errors="coerce")
            return df
        if "Cumplimiento_norm" in df.columns:
            df["cumplimiento_pct"] = pd.to_numeric(df["Cumplimiento_norm"], errors="coerce") * 100
            return df
        if "Cumplimiento Real" in df.columns:
            df["cumplimiento_pct"] = pd.to_numeric(df["Cumplimiento Real"], errors="coerce")
            return df
        return df

    cmi_global = _ensure_cumplimiento_pct(cmi_global)
    cmi_base = _ensure_cumplimiento_pct(cmi_base)

    st.caption(
        f"Fuente: Consolidado Semestral · Resultados Consolidados.xlsx — Corte: {mes} {anio}."
    )

    if cmi_global.empty:
        st.warning("No hay indicadores de CMI por Procesos para el corte seleccionado.")
        return

    pct_col = "cumplimiento_pct" if "cumplimiento_pct" in cmi_global.columns else "Cumplimiento_pct" if "Cumplimiento_pct" in cmi_global.columns else None
    proc_col_candidates = ["Proceso", "Proceso_x", "Proceso_y", "Subproceso_final", "Subproceso"]
    proc_col = next((col for col in proc_col_candidates if col in cmi_global.columns), "Subproceso")

    if pct_col is None:
        pct_col = "cumplimiento_pct"
        cmi_global["cumplimiento_pct"] = pd.NA
        cmi_base["cumplimiento_pct"] = pd.NA

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

    total_indicadores = int(cmi_global["Indicador"].nunique()) if "Indicador" in cmi_global.columns else len(cmi_global)
    total_procesos = int(proc_curr.shape[0])
    n_mejoran = int(proc_comp[proc_comp["delta_2024"] > 0].shape[0])
    n_empeoran = int(proc_comp[proc_comp["delta_2024"] < 0].shape[0])
    top_procesos = proc_comp.head(3)[proc_col].astype(str).tolist()

    overview_tab, unit_tab, frequency_tab, classification_tab, consolidated_tab = st.tabs([
        "Visión general",
        "Por Unidad",
        "Por Frecuencia",
        "Por Clasificación",
        "Consolidado",
    ])

    with overview_tab:
        st.markdown("### Visión general de CMI por Procesos")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Procesos analizados", f"{total_procesos}")
        k2.metric("Indicadores CMI", f"{total_indicadores}")
        k3.metric("Procesos con mejora", f"{n_mejoran}")
        k4.metric("Procesos en riesgo", f"{n_empeoran}")

        st.markdown("#### Comparativo por proceso")
        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                name=f"Cumplimiento {anio}",
                x=proc_comp[proc_col],
                y=proc_comp["actual"],
                marker_color=[_compliance_color(v) for v in proc_comp["actual"]],
                hovertemplate="%{x}<br>Cumplimiento: %{y:.3f}<extra></extra>",
            )
        )
        if "base_2024" in proc_comp.columns and proc_comp["base_2024"].notna().any():
            fig_bar.add_trace(
                go.Bar(
                    name=f"Cumplimiento {base_year}",
                    x=proc_comp[proc_col],
                    y=proc_comp["base_2024"],
                    marker_color="#9AB7D5",
                    hovertemplate="%{x}<br>Cumplimiento base: %{y:.3f}<extra></extra>",
                )
            )
        fig_bar.update_layout(
            barmode="group",
            height=400,
            margin=dict(t=30, b=130),
            xaxis_tickangle=-35,
            xaxis_title=proc_col,
            yaxis_title="Cumplimiento promedio",
            legend_title_text="Comparación histórica",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        if top_procesos:
            st.markdown("#### Procesos con mejor desempeño")
            st.write(", ".join(top_procesos[:3]))

    with unit_tab:
        st.markdown("### Informe por Unidad")
        unidad_summary = _build_unit_summary(cmi_global)
        if unidad_summary.empty:
            st.info("No hay datos disponibles para la agrupación por unidad.")
        else:
            st.dataframe(
                unidad_summary.sort_values(["cumplimiento", "indicadores"], ascending=[False, False]).head(50),
                use_container_width=True,
            )

    with frequency_tab:
        st.markdown("### Informe por Frecuencia")
        frecuencia_summary = _build_frequency_summary(cmi_global)
        if frecuencia_summary.empty:
            st.info("No hay datos disponibles para la agrupación por frecuencia.")
        else:
            st.dataframe(
                frecuencia_summary.sort_values(["Periodicidad", "Mes"], ascending=[True, True]).head(50),
                use_container_width=True,
            )

    with classification_tab:
        st.markdown("### Informe por Clasificación")
        clasificacion_summary = _build_classification_summary(cmi_global)
        if clasificacion_summary.empty:
            st.info("No hay datos de clasificación disponibles.")
        else:
            sort_keys = [c for c in ["Clasificacion", "Tipo de proceso"] if c in clasificacion_summary.columns]
            sort_keys.append("cumplimiento")
            st.dataframe(
                clasificacion_summary.sort_values(sort_keys, ascending=[True] * (len(sort_keys) - 1) + [False]).head(50),
                use_container_width=True,
            )

    with consolidated_tab:
        st.markdown("### Consolidado de indicadores CMI por Procesos")
        cols = _build_consolidated_columns(cmi_global)
        if not cols:
            st.info("No hay columnas disponibles para consolidar.")
        else:
            st.dataframe(cmi_global[cols].sort_values(["Proceso", "Subproceso"], ascending=True).head(100), use_container_width=True)

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
            proc_table[col] = pd.to_numeric(proc_table[col], errors="coerce").round(3)

    st.markdown("#### Tabla de comparación detallada")
    st.dataframe(proc_table, use_container_width=True, hide_index=True)
