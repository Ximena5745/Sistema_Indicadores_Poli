import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_cierres, load_worksheet_flags
from services.cmi_filters.loaders import load_cmi_worksheet

print('=== ANALIZAR ESTRUCTURA COMPLETA ===\n')

# Load all sources
ws_flags = load_worksheet_flags()
ws_cmi = load_cmi_worksheet()
cierres = load_cierres()

print(f'[1] Worksheet Flags: {len(ws_flags)} rows')
if not ws_flags.empty:
    print(f'    Columns: {list(ws_flags.columns)[:5]}...')
    print(f'    Proyecto=1 count: {(ws_flags["Proyecto"] == 1).sum() if "Proyecto" in ws_flags.columns else "N/A"}')

print(f'\n[2] Worksheet CMI: {len(ws_cmi)} rows')
if not ws_cmi.empty:
    print(f'    Columns: {list(ws_cmi.columns)[:5]}...')
    print(f'    Proyecto=1 count: {(ws_cmi["Proyecto"] == 1).sum() if "Proyecto" in ws_cmi.columns else "N/A"}')

print(f'\n[3] Cierres: {len(cierres)} rows')
print(f'    Columns: {list(cierres.columns)[:5]}...')

# Check if there's a relationship
print(f'\n[4] Check for ID relationship:')

# Try to find cierres that match ANY worksheet ID
if not ws_flags.empty and not cierres.empty and "Id" in ws_flags.columns and "Id" in cierres.columns:
    ws_ids = set(str(int(x)) if isinstance(x, float) else str(x).strip() for x in ws_flags['Id'].dropna())
    ce_ids = set(str(int(x)) if isinstance(x, float) else str(x).strip() for x in cierres['Id'].dropna())
    
    print(f'    Worksheet IDs: {len(ws_ids)}')
    print(f'    Cierres IDs: {len(ce_ids)}')
    print(f'    Overlap: {len(ws_ids & ce_ids)}')
    
    # Try reverse: check if cierres IDs can be found in Indicador names
    print(f'\n[5] Check Indicador names in Cierres:')
    print(f'    Sample Indicadores: {cierres["Indicador"].unique()[:3]}')

print('\n=== CONCLUSION ===')
print('Si no hay overlap, los cierres ya SON los proyectos')
print('No necesita filtrar - simplemente usar cierres directamente')
