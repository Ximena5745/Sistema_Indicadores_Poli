import os
import uuid
import pandas as pd
from streamlit_app.components import renderers
from core import db_manager


def test_save_excel_and_db_roundtrip():
    # preparar datos de prueba con marcador único
    marker = str(uuid.uuid4())
    df = pd.DataFrame([
        {"ACCION": "Test A", "RESPONSABLE": "CI", "ESTADO": "Abierta", "test_marker": marker},
        {"ACCION": "Test B", "RESPONSABLE": "CI", "ESTADO": "Abierta", "test_marker": marker},
    ])

    # Guardar Excel y verificar que el archivo existe y tiene contenido
    path = renderers._save_actions_to_excel(df, basename="test_actions_roundtrip")
    assert os.path.exists(path)
    # leer con pandas (openpyxl required)
    try:
        df_reload = pd.read_excel(path, engine='openpyxl')
        assert len(df_reload) == len(df)
    finally:
        # cleanup archivo
        try:
            os.remove(path)
        except Exception:
            pass

    # Insertar en DB y verificar lectura
    ok = db_manager.guardar_acciones_bulk(df)
    assert ok is True

    rows = db_manager.leer_acciones(limit=50)
    # filtrar por marcador
    found = [r for r in rows if r.get('test_marker') == marker]
    assert len(found) == len(df)

    # cleanup DB
    assert db_manager.borrar_acciones_por_marker('test_marker', marker) is True
