from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
import pandas as pd
from streamlit_app.services.data_service import DataService
from streamlit_app.pages.resumen_por_proceso import _mes_to_num, _prepare_tracking, _build_indicator_history

ds = DataService()
tracking_df = ds.get_tracking_data()
map_df = ds.get_process_map()
indicator_name = 'Aseguramiento de matrícula académica virtual'
rows = tracking_df[tracking_df['Indicador'].astype(str).str.contains(indicator_name, case=False, na=False)] if 'Indicador' in tracking_df.columns else pd.DataFrame()
print('matches', len(rows))
if not rows.empty:
    print('unique Mes:', rows['Mes'].astype(str).unique())
    print('unique Periodo:', rows['Periodo'].astype(str).unique())
    print('Periodo types:', rows['Periodo'].apply(lambda x: type(x).__name__).unique())
    print('first rows:')
    print(rows[['Id','Indicador','Mes','Periodo','Meta','Ejecucion','Ejecución','Periodicidad','Cumplimiento_pct']].head(20).to_string())
    print('Mes num:', rows['Mes'].apply(_mes_to_num).tolist())
    prep = _prepare_tracking(tracking_df, map_df, month_num=None)
    h = _build_indicator_history(prep, indicator_name)
    print('history sample rows', len(h))
    if not h.empty:
        print(h[['Anio','Mes','Mes_num','Periodo','Fecha','Meta','Ejecucion','Cumplimiento_pct']].head(20).to_string())
else:
    print('no matches')
