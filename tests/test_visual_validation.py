import pandas as pd
from pathlib import Path


def test_mapping_and_consolidado_exist():
    root = Path(__file__).resolve().parents[1]
    mapping = root / 'data' / 'output' / 'artifacts' / 'indicadores_cmi_mapping_v2.csv'
    consolidado = root / 'data' / 'output' / 'Resultados Consolidados.xlsx'
    assert mapping.exists(), f"Mapping file not found: {mapping}"
    assert consolidado.exists(), f"Consolidado file not found: {consolidado}"


def test_mapping_columns_and_merge():
    root = Path(__file__).resolve().parents[1]
    mapping = pd.read_csv(root / 'data' / 'output' / 'artifacts' / 'indicadores_cmi_mapping_v2.csv')
    mapping['Id'] = mapping['Id'].astype(str).str.replace(r'\.0$', '', regex=True)
    assert 'Id' in mapping.columns
    assert 'Indicador' in mapping.columns
    # Load consolidado and check expected columns
    # Prefer latest CSV if exists
    latest_csv = root / 'data' / 'output' / 'artifacts' / 'resultados_consolidados_latest.csv'
    if latest_csv.exists():
        dfc = pd.read_csv(latest_csv)
    else:
        xl = pd.ExcelFile(root / 'data' / 'output' / 'Resultados Consolidados.xlsx')
        dfc = xl.parse(xl.sheet_names[0])
    assert 'Id' in dfc.columns
    assert 'Cumplimiento' in dfc.columns
    assert 'Fecha' in dfc.columns
    dfc['Id'] = dfc['Id'].astype(str).str.replace(r'\.0$', '', regex=True)

    # Merge and ensure Cumplimiento column present after merge
    idx = dfc.groupby('Id')['Fecha'].idxmax()
    df_latest = dfc.loc[idx][['Id', 'Cumplimiento']]
    merged = mapping.merge(df_latest, on='Id', how='left')
    assert 'Cumplimiento' in merged.columns
