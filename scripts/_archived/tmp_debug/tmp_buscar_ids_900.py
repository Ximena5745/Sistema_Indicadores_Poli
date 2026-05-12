import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_worksheet_flags, load_cierres

print('=== BUSCAR IDS 900+ EN CIERRES ===\n')

# Get proyectos
ws = load_worksheet_flags()
proy_ws = ws[ws["Proyecto"] == 1].copy()
proy_ids = set(str(x).strip() for x in proy_ws["Id"].dropna())

print(f'[1] IDs de proyectos: {sorted(list(proy_ids))}')

# Get cierres
cierres = load_cierres()

# Try to convert cierres IDs to int to see if 900+ exist
cierres_ids_int = []
for id_val in cierres["Id"].dropna():
    try:
        cierres_ids_int.append(int(float(str(id_val))))
    except:
        pass

cierres_ids_int_set = set(cierres_ids_int)

print(f'\n[2] IDs en cierres (como int):')
print(f'    Mínimo: {min(cierres_ids_int_set)}')
print(f'    Máximo: {max(cierres_ids_int_set)}')
print(f'    ¿Hay en rango 900+? {any(x >= 900 for x in cierres_ids_int_set)}')

# Check specific IDs
proy_ids_900 = sorted([x for x in proy_ids if x.isdigit() and int(x) >= 900])
print(f'\n[3] Proyectos IDs 900+: {proy_ids_900}')

# Check if ANY of these 900+ IDs are in cierres
if proy_ids_900:
    proy_ids_900_int = set(int(x) for x in proy_ids_900)
    overlap_900 = proy_ids_900_int.intersection(cierres_ids_int_set)
    print(f'    En cierres: {len(overlap_900)}')
    if overlap_900:
        print(f'    Ejemplos: {list(overlap_900)[:5]}')

# Final: Todos los proyectos ids como int
proy_all_int = []
for x in proy_ids:
    if x not in ['10.1', '13.1']:  # skip decimales
        try:
            proy_all_int.append(int(x))
        except:
            pass

proy_all_int_set = set(proy_all_int)
overlap_all = proy_all_int_set.intersection(cierres_ids_int_set)

print(f'\n[4] RESULTADO FINAL: IDs proyectos que existen en cierres')
print(f'    Total proyectos (sin decimales): {len(proy_all_int_set)}')
print(f'    En cierres: {len(overlap_all)}')
if overlap_all:
    print(f'    Son estos: {sorted(list(overlap_all))}')
    
    # Si hay coincidencias, mostrar registros
    cierres_proy = cierres[cierres["Id"].astype(str).str.replace('.0', '').astype(int).isin(overlap_all)]
    print(f'\n[5] Cierres de proyectos: {len(cierres_proy)} registros')
    print(cierres_proy[["Id", "Indicador", "Meta", "Ejecucion", "cumplimiento_pct"]].head(10))
else:
    print(f'    NINGUNO - Los IDs de proyectos NO existen en cierres')
