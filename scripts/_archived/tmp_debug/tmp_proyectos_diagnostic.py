import sys
sys.path.insert(0, '.')
import pandas as pd

from streamlit_app.pages.resumen_general import _get_proyectos_ids
from services.strategic_indicators import load_cierres

print('=== DIAGNOSTICO: PROYECTOS ===\n')

# Get proyecto IDs
ids_proy = _get_proyectos_ids()
print(f'[1] IDs de Proyectos identificados: {len(ids_proy)}')
if ids_proy:
    print(f'    Ejemplos: {list(ids_proy)[:5]}...')

# Load cierres and filter
cierres = load_cierres()
print(f'\n[2] Total de Cierres: {len(cierres)}')

if ids_proy and not cierres.empty:
    # Normalize IDs
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
    cierres_copy['Id'] = cierres_copy['Id'].apply(_norm_id)
    
    # Filter
    cierres_proy = cierres_copy[cierres_copy['Id'].isin(ids_proy)].copy()
    print(f'[3] Cierres para Proyectos: {len(cierres_proy)}')
    
    # Filter by year
    cierres_proy_2025 = cierres_proy[cierres_proy['Anio'] == 2025]
    print(f'[4] Cierres para Proyectos (2025): {len(cierres_proy_2025)}')
    
    # Check cumplimiento column
    if 'cumplimiento_pct' in cierres_proy_2025.columns:
        print(f'[5] Cumplimiento column found: OK')
        print(f'    Non-null values: {cierres_proy_2025["cumplimiento_pct"].notna().sum()}')
    else:
        print(f'[5] Cumplimiento column NOT found')
        print(f'    Available columns: {list(cierres_proy_2025.columns[:10])}')
        
    print('\n=== CONCLUSION ===')
    print('Verificar que los proyectos estan siendo cargados correctamente')
else:
    print('[3] ERROR: No proyecto IDs or cierres')
