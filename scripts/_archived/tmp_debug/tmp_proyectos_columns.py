import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_worksheet_flags

# Load proyectos
ws = load_worksheet_flags()
proy = ws[ws["Proyecto"] == 1].copy()

print(f'=== PROYECTOS DATOS DISPONIBLES ===\n')
print(f'[1] Total columnas: {len(proy.columns)}')
print(f'[2] Todas las columnas:')
for col in proy.columns:
    non_null = proy[col].notna().sum()
    print(f'    - {col}: {non_null}/{len(proy)} non-null')

print(f'\n[3] Primeras 5 filas (primeras 8 columnas):')
print(proy.iloc[:5, :8])

print(f'\n[4] Buscando columnas de cumplimiento/ejecución:')
for col in proy.columns:
    if 'cumpl' in col.lower() or 'ejecuc' in col.lower() or 'meta' in col.lower():
        print(f'    - {col}: {proy[col].head(3).tolist()}')
