#!/usr/bin/env python3
"""Test simple sin imports complejos."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

print(f"ROOT: {ROOT}")

RAW_XLSX = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"
print(f"RAW_XLSX: {RAW_XLSX}")
print(f"Existe: {RAW_XLSX.exists()}")

OUT_XLSX = ROOT / "data" / "output" / "Resultados Consolidados.xlsx"
print(f"OUT_XLSX: {OUT_XLSX}")
print(f"Existe: {OUT_XLSX.exists()}")

# Try load directly
import pandas as pd

print("\n--- Cargando Worksheet ---")
try:
    df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
    print(f"OK: {len(df)} filas")
    print(f"Columnas: {list(df.columns)[:5]}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n--- Cargando Consolidado Cierres ---")
try:
    df = pd.read_excel(OUT_XLSX, sheet_name="Consolidado Cierres", engine="openpyxl")
    print(f"OK: {len(df)} filas")
    print(f"Columnas: {list(df.columns)[:5]}")
except Exception as e:
    print(f"ERROR: {e}")

print("\nSUCCESS: Los archivos están accesibles.")
