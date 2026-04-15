#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script detallado para examinar la estructura interna de los archivos Excel.
"""

import pandas as pd
from pathlib import Path
import sys
import io

# Fix encoding issues on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
        print(f"   [OK] Archivo encontrado: {cmi_file}")
        print(f"\n   Hojas disponibles ({len(xl.sheet_names)}):")
        for sheet in xl.sheet_names:
            try:
                df = xl.parse(sheet)
                print(f"     • {sheet}: {len(df)} filas x {len(df.columns)} columnas")
                cols_str = list(df.columns)[:10]
                tail_str = "..." if len(df.columns) > 10 else ""
                print(f"       Columnas: {cols_str}{tail_str}")
            except Exception as e:
                print(f"     • {sheet}: ERROR - {e}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
else:
    print(f"   [NOT FOUND] No encontrado: {cmi_file}")

# 2. Resultados Consolidados.xlsx
print("\n\n2. Resultados Consolidados.xlsx")
print("-" * 80)
consolidado = DATA_OUTPUT / "Resultados Consolidados.xlsx"
if consolidado.exists():
    try:
        xl = pd.ExcelFile(consolidado, engine="openpyxl")
        print(f"   ✅ Archivo encontrado: {consolidado}")
        print(f"\n   Hojas disponibles ({len(xl.sheet_names)}):")
        for sheet in xl.sheet_names:
            try:
                df = xl.parse(sheet)
                print(f"     • {sheet}: {len(df)} filas × {len(df.columns)} columnas")
                # Mostrar primeras 3 columnas como muestra
                cols_sample = list(df.columns)[:3]
                print(f"       Primeras columnas: {cols_sample}")
                
                # Para Consolidado Cierres, mostrar si tiene datos de 2025
                if 'Consolidado Cierres' in sheet:
                    if any(col for col in df.columns if 'año' in col.lower() or 'anio' in col.lower()):
                        año_cols = [c for c in df.columns if 'año' in c.lower() or 'anio' in c.lower()]
                        print(f"       Años únicos en {año_cols}: {df[año_cols[0]].dropna().unique()[:5]}")
                    
            except Exception as e:
                print(f"     • {sheet}: ERROR - {e}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print(f"   ❌ No encontrado: {consolidado}")

# 3. Indicadores por CMI.xlsx - revisión específica de hojas clave
print("\n\n3. REVISIÓN DETALLADA: Hojas clave en CMI")
print("-" * 80)
if cmi_file.exists():
    try:
        xl = pd.ExcelFile(cmi_file, engine="openpyxl")
        
        # Buscar hojas que contengan lo que necesitamos
        hojas_de_interes = ['worksheet', 'pdi', 'cna', 'catalogo', 'indicadores']
        for pattern in hojas_de_interes:
            matching = [s for s in xl.sheet_names if pattern.lower() in s.lower()]
            if matching:
                print(f"\n   Hojas que contienen '{pattern}':")
                for sheet in matching:
                    try:
                        df = xl.parse(sheet)
                        print(f"     • {sheet}")
                        if not df.empty:
                            # Mostrar estadísticas útiles
                            if 'id' in [c.lower() for c in df.columns]:
                                id_col = next(c for c in df.columns if c.lower() == 'id')
                                print(f"       - Registros: {len(df)}")
                                print(f"       - IDs no nulos: {df[id_col].notna().sum()}")
                            
                            # Columnas importantes
                            important_cols = ['id', 'indicador', 'linea', 'objetivo', 'flagplanestrategico', 'proyecto']
                            found_cols = [c for c in df.columns if c.lower() in important_cols]
                            if found_cols:
                                print(f"       - Columnas importantes encontradas: {found_cols}")
                    except Exception as e:
                        print(f"     • {sheet}: ERROR al parsear - {str(e)[:50]}")
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "="*80)
