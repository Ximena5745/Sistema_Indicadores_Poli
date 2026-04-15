#!/usr/bin/env python3
"""Ver todas las columnas de las hojas clave."""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_OUTPUT = ROOT / "data" / "output"

print("\n" + "="*80)
print("TODAS LAS COLUMNAS DE HOJAS CLAVE")
print("="*80)

# 1. Worksheet en CMI
print("\n1. Indicadores por CMI.xlsx - Worksheet")
print("-" * 80)
cmi_file = DATA_RAW / "Indicadores por CMI.xlsx"
try:
    df = pd.read_excel(cmi_file, sheet_name="Worksheet", engine="openpyxl")
    print(f"Filas: {len(df)}, Columnas: {len(df.columns)}")
    print(f"\nTodas las columnas ({len(df.columns)}):")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
except Exception as e:
    print(f"ERROR: {e}")

# 2. Consolidado Cierres
print("\n\n2. Resultados Consolidados.xlsx - Consolidado Cierres")
print("-" * 80)
consolidado = DATA_OUTPUT / "Resultados Consolidados.xlsx"
try:
    df = pd.read_excel(consolidado, sheet_name="Consolidado Cierres", engine="openpyxl")
    print(f"Filas: {len(df)}, Columnas: {len(df.columns)}")
    print(f"\nTodas las columnas ({len(df.columns)}):")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*80)
