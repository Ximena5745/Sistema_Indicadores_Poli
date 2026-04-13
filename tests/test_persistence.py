import os
import pandas as pd
from core import db_manager
from streamlit_app.components import renderers


def test_save_csv_and_remove():
    df = pd.DataFrame([{"ACCION": "A", "ESTADO": "Abierta"}])
    path = renderers._save_actions_to_excel(df, basename="test_persist")
    assert os.path.exists(path)
    # cleanup
    try:
        os.remove(path)
    except Exception:
        pass


def test_db_bulk_insert():
    df = pd.DataFrame([{"ACCION": "B", "ESTADO": "Abierta"}])
    ok = db_manager.guardar_acciones_bulk(df)
    assert ok is True
