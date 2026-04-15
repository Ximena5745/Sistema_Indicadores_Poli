#!/usr/bin/env python3
"""Verificar el cálculo de ROOT en strategic_indicators."""

from pathlib import Path

# El archivo está en root/services/strategic_indicators.py
file = Path("c:/Users/ximen/OneDrive/Proyectos_DS/Sistema_Indicadores_Poli/services/strategic_indicators.py")

# Simulate: ROOT = Path(__file__).resolve().parents[2]
ROOT = file.parents[2]
print(f"File: {file}")
print(f"Calculated ROOT = parents[2]: {ROOT}")

RAW_XLSX = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"
print(f"RAW_XLSX: {RAW_XLSX}")
print(f"Exists: {RAW_XLSX.exists()}")

# Correct path should be parents[1]
ROOT_CORRECT = file.parents[1]
print(f"\nCorrect ROOT = parents[1]: {ROOT_CORRECT}")
RAW_XLSX_CORRECT = ROOT_CORRECT / "data" / "raw" / "Indicadores por CMI.xlsx"
print(f"RAW_XLSX correct: {RAW_XLSX_CORRECT}")
print(f"Exists: {RAW_XLSX_CORRECT.exists()}")
