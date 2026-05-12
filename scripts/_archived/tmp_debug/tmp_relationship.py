import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_worksheet_flags, load_cierres

# Load data
ws = load_worksheet_flags()
cierres = load_cierres()

print('=== BUSCAR RELACION ===\n')

# Check if Indicador in worksheet matches Indicador in cierres
print('[1] Indicadores en Worksheet (Proyecto=1):')
ws_proy = ws[ws['Proyecto'] == 1]
print(f'    Total: {len(ws_proy)}')
if 'Indicador' in ws_proy.columns:
    print(f'    Ejemplos indicadores: {ws_proy["Indicador"].head(3).tolist()}')

print(f'\n[2] Indicadores en Cierres:')
print(f'    Total: {len(cierres["Indicador"].unique())}')
print(f'    Ejemplos: {cierres["Indicador"].unique()[:3]}')

# Try to match by Indicador name
if 'Indicador' in ws_proy.columns:
    ws_ind_set = set(ws_proy['Indicador'].dropna().unique())
    ci_ind_set = set(cierres['Indicador'].dropna().unique())
    
    overlap_ind = ws_ind_set.intersection(ci_ind_set)
    print(f'\n[3] Indicadores que coinciden por nombre: {len(overlap_ind)}')
    if overlap_ind:
        print(f'    Ejemplos: {list(overlap_ind)[:3]}')

# Maybe the connection is through something else
print(f'\n[4] Check Cierres columns for tipo/clasificacion:')
for col in cierres.columns:
    if 'tipo' in col.lower() or 'clasif' in col.lower() or 'categoria' in col.lower():
        print(f'    - {col}: {cierres[col].unique()[:3]}')

print('\n=== TEORÍA ===')
print('Si los Indicadores NO coinciden, entonces "Proyectos" en cierres')
print('son un conjunto DIFERENTE de datos que NO se filtra por Proyecto=1')
