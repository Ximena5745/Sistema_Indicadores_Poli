import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_worksheet_flags, load_cierres

print('=== AUDITORIA CORRECTA: PROYECTOS EN CIERRES ===\n')

# Get proyectos del worksheet
ws = load_worksheet_flags()
proy_ws = ws[ws["Proyecto"] == 1].copy()

print(f'[1] Proyectos en worksheet: {len(proy_ws)}')
print(f'    IDs: {sorted(proy_ws["Id"].unique())[:10]}...')

# Get cierres
cierres = load_cierres()
print(f'\n[2] Total cierres: {len(cierres)}')

# Get IDs únicos en cierres
cierres_ids = set(cierres["Id"].unique())
print(f'    IDs únicos: {len(cierres_ids)}')
print(f'    Ejemplos IDs: {sorted(list(cierres_ids))[:10]}...')

# Check if ANY proyecto IDs exist in cierres (sin normalización)
ws_ids_str = set(str(x) for x in proy_ws["Id"].dropna())
proy_in_cierres = ws_ids_str.intersection(cierres_ids)

print(f'\n[3] Proyectos IDs que existen en cierres (directos): {len(proy_in_cierres)}')
if proy_in_cierres:
    print(f'    Ejemplos: {list(proy_in_cierres)[:5]}')

# Try with string conversion from cierres
cierres_ids_str = set(str(int(x)) if isinstance(x, float) else str(x) 
                      for x in cierres["Id"].dropna())
proy_in_cierres_v2 = ws_ids_str.intersection(cierres_ids_str)

print(f'\n[4] Con conversión a int de cierres: {len(proy_in_cierres_v2)}')
if proy_in_cierres_v2:
    print(f'    Ejemplos: {list(proy_in_cierres_v2)[:5]}')

# Check cierres filtered by proyecto IDs
if proy_in_cierres_v2:
    cierres_proy = cierres[cierres["Id"].isin(proy_in_cierres_v2)]
    print(f'\n[5] Cierres con proyecto IDs: {len(cierres_proy)}')
    print(f'    Campos disponibles: {list(cierres_proy.columns)[:10]}')
    print(f'    Ejemplo fila:')
    print(cierres_proy[["Id", "Indicador", "Meta", "Ejecucion", "cumplimiento_pct"]].head(1))

print('\n=== CONCLUSIÓN ===')
print('¿Los proyectos SÍ están en cierres? Usar la respuesta arriba para corregir')
