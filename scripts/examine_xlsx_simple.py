#!/usr/bin/env python3
"""Examinar estructura de archivos Excel sin emojis."""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_OUTPUT = ROOT / "data" / "output"

print("\n" + "="*80)
print("ESTRUCTURA DE ARCHIVOS EXCEL")
print("="*80)

# 1. Indicadores por CMI.xlsx
print("\n1. Indicadores por CMI.xlsx")
print("-" * 80)
cmi_file = DATA_RAW / "Indicadores por CMI.xlsx"
if cmi_file.exists():
    try:
        xl = pd.ExcelFile(cmi_file, engine="openpyxl")
        print(f"[OK] Archivo encontrado")
        print(f"\nHojas disponibles ({len(xl.sheet_names)}):")
        for sheet in xl.sheet_names:
            try:
                df = xl.parse(sheet)
                print(f"  {sheet}: {len(df)} filas, {len(df.columns)} cols")
                print(f"    Columnas: {list(df.columns)[:5]}")
            except Exception as e:
                print(f"  {sheet}: ERROR - {str(e)[:50]}")
    except Exception as e:
        print(f"[ERROR] {e}")
else:
    print(f"[NOT FOUND]")

# 2. Resultados Consolidados.xlsx
print("\n\n2. Resultados Consolidados.xlsx")
print("-" * 80)
consolidado = DATA_OUTPUT / "Resultados Consolidados.xlsx"
if consolidado.exists():
    try:
        xl = pd.ExcelFile(consolidado, engine="openpyxl")
        print(f"[OK] Archivo encontrado")
        print(f"\nHojas disponibles ({len(xl.sheet_names)}):")
        for sheet in xl.sheet_names:
            try:
                df = xl.parse(sheet)
                print(f"  {sheet}: {len(df)} filas, {len(df.columns)} cols")
                print(f"    Columnas: {list(df.columns)[:5]}")
            except Exception as e:
                print(f"  {sheet}: ERROR - {str(e)[:50]}")
    except Exception as e:
        print(f"[ERROR] {e}")
else:
    print(f"[NOT FOUND]")

print("\n" + "="*80)
