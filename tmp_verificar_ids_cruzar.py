import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_worksheet_flags, load_cierres

print('=== VERIFICACION: IDS PROYECTOS EN CIERRES ===\n')

# [1] Cargar Indicadores por CMI y filtrar Proyectos=1
ws = load_worksheet_flags()
proy_ws = ws[ws["Proyecto"] == 1].copy()

print(f'[1] Proyectos en Indicadores por CMI (Proyecto=1):')
print(f'    Total: {len(proy_ws)}')
print(f'    IDs (sin normalizar): {proy_ws["Id"].unique()[:10]}')
print(f'    Tipo de IDs: {type(proy_ws["Id"].iloc[0])}')

# [2] Cargar Consolidado Cierres
cierres = load_cierres()
print(f'\n[2] Consolidado Cierres:')
print(f'    Total filas: {len(cierres)}')
print(f'    IDs únicos: {cierres["Id"].nunique()}')
print(f'    Ejemplos IDs (sin normalizar): {cierres["Id"].unique()[:10]}')
print(f'    Tipo de IDs: {type(cierres["Id"].iloc[0])}')

# [3] Intentar cruzar DIRECTAMENTE sin normalizar
print(f'\n[3] Intento 1: Cruzar DIRECTAMENTE (sin normalizar)')
proy_ids_direct = set(proy_ws["Id"].dropna())
cierres_ids_direct = set(cierres["Id"].dropna())
overlap_direct = proy_ids_direct.intersection(cierres_ids_direct)
print(f'    Proyectos IDs: {proy_ids_direct}')
print(f'    Cierres IDs (muestra): {sorted(list(cierres_ids_direct))[:15]}')
print(f'    Coincidencias: {len(overlap_direct)}')

# [4] Normalizar: convertir todo a string
print(f'\n[4] Intento 2: Normalizar a STRING')
proy_ids_str = set(str(x).strip() for x in proy_ws["Id"].dropna())
cierres_ids_str = set(str(x).strip() for x in cierres["Id"].dropna())
overlap_str = proy_ids_str.intersection(cierres_ids_str)
print(f'    Proyectos IDs (str): {sorted(proy_ids_str)[:10]}')
print(f'    Cierres IDs (str) muestra: {sorted(list(cierres_ids_str))[:10]}')
print(f'    Coincidencias: {len(overlap_str)}')
if overlap_str:
    print(f'    Ejemplos: {list(overlap_str)[:5]}')

# [5] Si hay coincidencias, filtrar cierres
if overlap_str:
    print(f'\n[5] RESULTADO: Filtrando cierres por IDs de proyectos')
    cierres_proy = cierres[cierres["Id"].astype(str).isin(overlap_str)]
    print(f'    Cierres filtrados: {len(cierres_proy)}')
    print(f'    Columnas: {list(cierres_proy.columns[:10])}')
    print(f'    Ejemplos:')
    print(cierres_proy[["Id", "Indicador", "cumplimiento_pct"]].head(5))
else:
    print(f'\n[5] PROBLEMA: No hay coincidencias de IDs')
    print(f'    ¿Los IDs en Indicadores por CMI existen en Cierres?')
    print(f'    Proyectos IDs: {sorted(list(proy_ids_str))[:15]}')
    print(f'    ¿Están estos en cierres?')
