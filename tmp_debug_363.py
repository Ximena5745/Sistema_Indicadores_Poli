from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from services.cmi_filters import filter_df_for_procesos
from streamlit_app.pages.informe_por_procesos import _prepare_tracking
from streamlit_app.services.data_service import DataService

ds = DataService()
tracking_df = ds.get_tracking_data()
map_df = ds.get_process_map()
print('tracking rows', len(tracking_df), 'map rows', len(map_df))
rows = tracking_df[tracking_df['Id'].astype(str).str.strip() == '363'] if 'Id' in tracking_df.columns else tracking_df.iloc[0:0]
print('rows for 363:', len(rows))
print(rows[['Id','Indicador','Subproceso_final','Proceso_padre','Subproceso','Tipo de proceso']].head(20).to_dict('records'))
full = _prepare_tracking(tracking_df, map_df, month_num=None)
print('full prepped', len(full), 'id363', len(full[full['Id'].astype(str).str.strip() == '363']))
filtered = filter_df_for_procesos(full, id_column='Id')
print('after cmi procesos filter', len(filtered), 'id363', len(filtered[filtered['Id'].astype(str).str.strip() == '363']))
print('filtered columns', list(filtered.columns))
