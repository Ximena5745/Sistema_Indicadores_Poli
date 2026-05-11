"""Utilities for tablero_operativo page."""

import unicodedata
import pandas as pd
import plotly.graph_objects as go

from streamlit_app.pages.tablero_operativo_config import (
    ARTIFACTS,
    MESES,
    MES_NUM,
    NIVEL_COLOR_EXT,
    NIVEL_ICON_EXT,
    ORDEN_SEV,
    VENTANA_MESES,
)


def normalize_string(s: str) -> str:
    """Normalize string by removing accents and converting to lowercase.
    
    Args:
        s: String to normalize
    
    Returns:
        Normalized string
    """
    if not isinstance(s, str):
        return str(s).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.strip().lower()


def get_ventana(periodicidad: str) -> int:
    """Get window in months for periodicity.
    
    Args:
        periodicidad: Periodicity name
    
    Returns:
        Window in months
    """
    return VENTANA_MESES.get(periodicidad, 12)


def load_base() -> pd.DataFrame:
    """Load base tracking data.
    
    Returns:
        DataFrame with tracking data
    """
    from streamlit_app.services.data_service import DataService
    
    ds = DataService()
    return ds.get_tracking_data()


def load_qc_artifacts() -> list[dict]:
    """Load quality artifacts from output directory.
    
    Returns:
        List of artifact dictionaries
    """
    import json
    from pathlib import Path
    
    artifacts = []
    if ARTIFACTS.exists():
        for f in ARTIFACTS.glob("*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    artifacts.append({"file": f.name, "data": data})
            except (json.JSONDecodeError, IOError):
                pass
    return artifacts


def prepare_tracking_df(
    df: pd.DataFrame,
    map_df: pd.DataFrame,
    mes_actual: int,
    anio_actual: int,
) -> pd.DataFrame:
    """Prepare tracking DataFrame with all columns and filters.
    
    Args:
        df: Tracking data
        map_df: Process map
        mes_actual: Current month number
        anio_actual: Current year
    
    Returns:
        Prepared tracking DataFrame
    """
    from streamlit_app.pages.resumen_por_proceso import _prepare_tracking
    from services.cmi_filters import filter_df_for_procesos
    
    df_prep = _prepare_tracking(df, map_df, month_num=mes_actual)
    df_prep = filter_df_for_procesos(df_prep, id_column="Id", map_df=map_df)
    return df_prep


def detect_overdue_indicators(df: pd.DataFrame, mes_actual: int, anio_actual: int) -> pd.DataFrame:
    """Detect overdue and at-risk indicators based on periodicity and reporting window.
    
    Args:
        df: Tracking DataFrame
        mes_actual: Current month
        anio_actual: Current year
    
    Returns:
        DataFrame with indicator status and days overdue
    """
    results = []
    
    for idx, row in df.iterrows():
        indicador_id = row.get("Id")
        periodicidad = row.get("Periodicidad")
        ventana = get_ventana(str(periodicidad or ""))
        
        # Find last reported month/year
        last_mes = row.get("Mes")
        last_anio = row.get("Anio")
        
        if pd.isna(last_mes) or pd.isna(last_anio):
            results.append({
                "Id": indicador_id,
                "Status": "Pendiente",
                "DaysOverdue": None,
            })
            continue
        
        last_mes_num = int(last_mes)
        last_anio_num = int(last_anio)
        
        # Calculate months since last report
        mes_diff = (anio_actual - last_anio_num) * 12 + (mes_actual - last_mes_num)
        
        if mes_diff > ventana:
            results.append({
                "Id": indicador_id,
                "Status": "Vencido",
                "DaysOverdue": mes_diff,
            })
        elif mes_diff >= (ventana * 0.8):
            results.append({
                "Id": indicador_id,
                "Status": "Alerta",
                "DaysOverdue": mes_diff,
            })
        else:
            results.append({
                "Id": indicador_id,
                "Status": "Al día",
                "DaysOverdue": mes_diff,
            })
    
    return pd.DataFrame(results)


def build_donut_chart(df: pd.DataFrame) -> go.Figure:
    """Build donut chart showing level distribution.
    
    Args:
        df: DataFrame with compliance data
    
    Returns:
        Plotly figure
    """
    niveles = df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=niveles.index,
        values=niveles.values,
        hole=0.4,
        marker=dict(colors=[NIVEL_COLOR_EXT.get(n, "#999") for n in niveles.index]),
    )])
    
    fig.update_layout(
        title="Distribución de niveles",
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    
    return fig


def build_process_chart(df: pd.DataFrame) -> go.Figure:
    """Build bar chart showing compliance by process.
    
    Args:
        df: DataFrame with process and compliance data
    
    Returns:
        Plotly figure
    """
    by_proceso = (
        df.groupby("Proceso_padre", dropna=False)["Cumplimiento_pct"]
        .mean()
        .fillna(0)
        .sort_values(ascending=False)
        .reset_index()
    )
    
    fig = go.Figure(data=[go.Bar(
        x=by_proceso["Cumplimiento_pct"],
        y=by_proceso["Proceso_padre"],
        orientation="h",
        marker=dict(color=by_proceso["Cumplimiento_pct"], colorscale="RdYlGn"),
    )])
    
    fig.update_layout(
        title="Cumplimiento promedio por proceso",
        xaxis_title="Cumplimiento (%)",
        yaxis_title="Proceso",
        height=300,
        margin=dict(l=100, r=10, t=40, b=10),
    )
    
    return fig
