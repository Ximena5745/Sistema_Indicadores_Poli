from pathlib import Path
import sys
import pandas as pd

# Ensure repo root in sys.path for simple imports when running in VSCode/Streamlit
ROOT = Path(__file__).parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.mock.mock_data import timeseries_fixture, semaforo_fixture

try:
    from services.data_loader import cargar_dataset
except (ImportError, ModuleNotFoundError):
    from ..services.data_loader import cargar_dataset


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
            return df[
                [
                    c
                    for c in ["Unidad", "Proceso", "Subproceso", "Tipo de proceso"]
                    if c in df.columns
                ]
            ].dropna(how="all")
        except Exception:
            return pd.DataFrame()

    def get_tracking_data(self) -> pd.DataFrame:
        """
        Carga datos de seguimiento desde Resultados Consolidados.xlsx - Consolidado Semestral.

        Según documentación oficial (docs/archive/FUENTES_POR_PAGINA.md):
        - Resumen por Proceso debe usar "Consolidado Semestral"
        - No usar "Seguimiento_Reporte.xlsx" para Meta/Ejecución/Cumplimiento

        Returns:
            DataFrame con: Id, Indicador, Proceso, Meta, Ejecucion, Cumplimiento, Año, Mes
        """
        try:
            # Usar la función oficial que lee Consolidado Semestral
            df = cargar_dataset()

            if df.empty:
                return pd.DataFrame()

            # Asegurar tipos de datos correctos (columnas vienen de cargar_dataset)
            # Ya vienen con tipos correctos: Anio=Int64, Mes=string
            # No necesita conversión adicional

            return df
        except Exception:
            return pd.DataFrame()
