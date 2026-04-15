#!/usr/bin/env python3
"""Validación final que el código funciona."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.strategic_indicators import (
    load_worksheet_flags,
    load_cierres, 
    preparar_pdi_con_cierre,
)

print("Iniciando validación...")

# 1. Load flags sin caché
print("\n1. Cargando worksheet flags...")
flags = load_worksheet_flags()
print(f"   OK: {len(flags)} registros")

# 2. Load cierres sin caché  
print("\n2. Cargando cierres...")
cierres = load_cierres()
print(f"   OK: {len(cierres)} registros")

# 3. Full PDI
print("\n3. Preparar PDI 2025-12...")
pdi = preparar_pdi_con_cierre(2025, 12)
print(f"   OK: {len(pdi)} registros")

if pdi.empty:
    print("   ERROR: PDI vacío!")
    exit(1)

# Verificaciones
pdi_ids = pdi["Linea"].nunique()
pdi_objs = pdi["Objetivo"].nunique()
print(f"\nResultados:")
print(f"   Líneas: {pdi_ids}")
print(f"   Objetivos: {pdi_objs}")
print(f"   Total indicadores: {len(pdi)}")

print("\nSUCCESS: La cadena de carga funciona correctamente.")
