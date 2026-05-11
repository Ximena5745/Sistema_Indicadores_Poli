import sys
sys.path.insert(0, '.')
import pandas as pd

from streamlit_app.pages.resumen_general import _get_proyectos_ids
from services.strategic_indicators import load_cierres

print('=== DIAGNOSTICO: DISCREPANCIA DE IDs ===\n')

# Get proyecto IDs from worksheet
ids_proy = _get_proyectos_ids()
print(f'[1] IDs en Worksheet como Proyectos: {len(ids_proy)}')
print(f'    Primeros 10: {sorted(list(ids_proy))[:10]}')

# Get cierres and check their IDs
cierres = load_cierres()
print(f'\n[2] IDs únicos en Cierres: {len(cierres["Id"].unique())}')

# Normalize IDs in cierres
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
cierres_copy['Id_normalized'] = cierres_copy['Id'].apply(_norm_id)
unique_normalized = set(cierres_copy['Id_normalized'].dropna().unique())

print(f'    Primeros 10 IDs en cierres: {sorted(list(unique_normalized))[:10]}')

# Check overlap
overlap = ids_proy.intersection(unique_normalized)
print(f'\n[3] IDs que coinciden entre Proyectos y Cierres: {len(overlap)}')
if overlap:
    print(f'    Ejemplos: {list(overlap)[:5]}')
else:
    print('    NO HAY COINCIDENCIAS - Este es el problema!')

# Analizar lo que hay
print(f'\n[4] Analisis:')
print(f'    IDs solo en Proyectos: {len(ids_proy - unique_normalized)}')
print(f'    IDs solo en Cierres: {len(unique_normalized - ids_proy)}')

# Muestra qué es lo que sí está en los cierres
print(f'\n[5] Tipos de IDs en Cierres:')
for id_val in sorted(list(unique_normalized))[:20]:
    print(f'    - {id_val}')

print('\n=== CONCLUSION ===')
print('Los IDs de proyectos en worksheet no coinciden con los IDs en cierres')
print('Esto significa que la tabla de worksheet tiene IDs diferentes a la de cierres')
