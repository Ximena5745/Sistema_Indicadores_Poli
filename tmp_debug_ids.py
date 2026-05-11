import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_cierres, load_worksheet_flags
from streamlit_app.pages.resumen_general import _get_proyectos_ids

# Test IDs
ids_proy_raw = _get_proyectos_ids()
print(f'=== DEBUG IDs ===\n')
print(f'[1] _get_proyectos_ids() retorna: {len(ids_proy_raw)}')
print(f'    Primeros 5: {sorted(list(ids_proy_raw))[:5]}')
print(f'    Tipos: {[type(x).__name__ for x in list(ids_proy_raw)[:3]]}')

# Get cierres
cierres = load_cierres()
print(f'\n[2] Cierres IDs (raw):')
print(f'    Primeros 5: {cierres["Id"].head(5).tolist()}')
print(f'    Tipos: {[type(x).__name__ for x in cierres["Id"].head(3)]}')

# Normalize as code does
def _norm_id(v):
    if pd.isna(v):
        return ""
    text = str(v).strip()
    try:
        num = float(text)
        if num.is_integer():
            return str(int(num))
    except:
        pass
    return text

cierres_copy = cierres.copy()
cierres_copy['Id_norm'] = cierres_copy['Id'].apply(_norm_id)

print(f'\n[3] Cierres IDs (after norm):')
print(f'    Primeros 5: {cierres_copy["Id_norm"].head(5).tolist()}')

# Filter
cierres_proy = cierres_copy[cierres_copy['Id_norm'].isin(ids_proy_raw)]
print(f'\n[4] Cierres que matchean con _get_proyectos_ids(): {len(cierres_proy)}')

# Debug: check if ANY of the proyecto IDs are in cierres
ce_ids_set = set(cierres_copy['Id_norm'].dropna())
proyectos_ids_set = set(ids_proy_raw)
overlap = proyectos_ids_set.intersection(ce_ids_set)

print(f'\n[5] Debugging overlap:')
print(f'    IDs proyectos: {sorted(list(proyectos_ids_set))[:10]}')
print(f'    IDs cierres: {sorted(list(ce_ids_set))[:10]}')
print(f'    Overlap: {len(overlap)} items')
if overlap:
    print(f'    Ejemplos overlap: {list(overlap)[:5]}')
