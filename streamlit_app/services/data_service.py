from pathlib import Path
import sys
import pandas as pd

# Ensure repo root in sys.path for simple imports when running in VSCode/Streamlit
ROOT = Path(__file__).parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.mock.mock_data import timeseries_fixture, semaforo_fixture


class DataService:
    """Simple data service to provide fixtures. Replace with real connectors later."""

    def get_timeseries(self) -> pd.DataFrame:
        return timeseries_fixture()

    def get_semaforo(self) -> pd.DataFrame:
        return semaforo_fixture()

    def get_process_map(self) -> pd.DataFrame:
        source = Path(__file__).parents[2] / "data" / "raw" / "Subproceso-Proceso-Area.xlsx"
        if not source.exists():
            return pd.DataFrame()

        try:
            xl = pd.ExcelFile(str(source), engine="openpyxl")
            if "Proceso" not in xl.sheet_names:
                return pd.DataFrame()
            df = xl.parse("Proceso")
            df.columns = [str(c).strip() for c in df.columns]
            return df[[c for c in ["Unidad", "Proceso", "Subproceso", "Tipo de proceso"] if c in df.columns]].dropna(how="all")
        except Exception:
            return pd.DataFrame()

    def get_tracking_data(self) -> pd.DataFrame:
        source = Path(__file__).parents[2] / "data" / "output" / "Seguimiento_Reporte.xlsx"
        if not source.exists():
            return pd.DataFrame()

        try:
            xl = pd.ExcelFile(str(source), engine="openpyxl")
            if "Tracking Mensual" not in xl.sheet_names:
                return pd.DataFrame()
            df = xl.parse("Tracking Mensual")
            df.columns = [str(c).strip() for c in df.columns]
            if "Año" in df.columns:
                df["Año"] = pd.to_numeric(df["Año"], errors="coerce").astype("Int64")
            if "Mes" in df.columns:
                df["Mes"] = pd.to_numeric(df["Mes"], errors="coerce").astype("Int64")
            return df
        except Exception:
            return pd.DataFrame()
