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
