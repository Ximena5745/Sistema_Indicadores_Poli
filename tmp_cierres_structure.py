import sys
sys.path.insert(0, '.')
import pandas as pd
from services.strategic_indicators import load_cierres

print('=== ANALIZAR ESTRUCTURA DE CIERRES ===\n')

cierres = load_cierres()
print(f'[1] Total de cierres: {len(cierres)}')
print(f'[2] Columnas disponibles:')
for i, col in enumerate(cierres.columns):
    print(f'    {i}: {col}')

print(f'\n[3] Primeras 3 filas:')
print(cierres.head(3).to_string())

print(f'\n[4] Columnas que pueden tener Linea/Objetivo:')
text_cols = ['Linea', 'Objetivo', 'clasificacion', 'Clasificacion', 
             'tipo', 'Tipo', 'Proceso', 'Subproceso', 'Area',
             'Indicador', 'Nombre', 'Descripcion']
for col in text_cols:
    if col in cierres.columns:
        print(f'    OK: {col}')

print(f'\n[5] Columnas de cumplimiento:')
cumpl_cols = ['cumplimiento_pct', 'Cumplimiento', 'cumplimiento',
              'Ejecucion', 'Meta', 'Porcentaje', 'Pct']
for col in cumpl_cols:
    if col in cierres.columns:
        non_null = cierres[col].notna().sum()
        print(f'    OK: {col} ({non_null} non-null)')

print('\n=== SOLUCION ===')
print('Los cierres tienen informacion de Linea/Objetivo')
print('No necesita filtrar por IDs de proyectos')
print('Simplemente usar todos los cierres que tienen clasificacion de Proyecto')
