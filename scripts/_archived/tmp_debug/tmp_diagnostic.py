import sys
sys.path.insert(0, '.')
import pandas as pd

print('=== DIAGNOSTICO DE DATOS EN RESUMEN GENERAL ===\n')

# Import data loading functions
from services.strategic_indicators import (
    preparar_pdi_con_cierre, load_pdi_catalog, load_cierres, load_worksheet_flags
)
from services.cmi_filters import filter_df_for_cmi_estrategico

print('[1] Cargar Indicadores PDI...')
pdi_base = preparar_pdi_con_cierre(2025, 12)
print(f'    PDI base cargados: {len(pdi_base) if pdi_base is not None else 0} filas')
if pdi_base is not None and not pdi_base.empty:
    pdi_estrat = filter_df_for_cmi_estrategico(pdi_base.copy())
    print(f'    Despues filtrar CMI Estrategico: {len(pdi_estrat)} filas')

print('\n[2] Cargar Cierres (Proyectos)...')
cierres = load_cierres()
print(f'    Cierres cargados: {len(cierres) if not cierres.empty else 0} filas')
if not cierres.empty:
    years = sorted(cierres['Anio'].unique()) if 'Anio' in cierres.columns else []
    print(f'    Anos en datos: {years}')
    if 'Anio' in cierres.columns:
        print(f'    Total por ano:')
        for year in years:
            count = len(cierres[cierres['Anio'] == year])
            print(f'      {int(year)}: {count} registros')

print('\n[3] Cargar Worksheet Flags...')
flags = load_worksheet_flags()
print(f'    Flags cargados: {len(flags) if not flags.empty else 0} filas')
if not flags.empty and 'Proyecto' in flags.columns:
    proy_count = (flags['Proyecto'] == 1).sum()
    print(f'    Registros marcados como Proyecto: {proy_count}')

print('\n=== STATUS ===')
print('Datos disponibles para cargar en dashboard')
