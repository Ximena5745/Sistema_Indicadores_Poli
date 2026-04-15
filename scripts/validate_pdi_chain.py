#!/usr/bin/env python3
"""Validación final: cadena completa de carga hasta preparar_pdi_con_cierre()."""

import sys
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

print("\n" + "="*80)
print("VALIDACIÓN FINAL: Cadena completa de carga de PDI")
print("="*80)

# Cargar manualmente bypass del caché
from core.config import DATA_RAW, DATA_OUTPUT
import unicodedata

def _norm_text(value: str) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

def _find_col(df: pd.DataFrame, names: list[str]) -> str | None:
    lookup = {_norm_text(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(_norm_text(name))
        if hit:
            return hit
    return None

def _id_limpio(x) -> str:
    if pd.isna(x):
        return ""
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x).strip()

# PASO 1: Cargar Worksheet
print("\n1. Cargar Worksheet (Indicadores por CMI.xlsx)...")
cmi_file = DATA_RAW / "Indicadores por CMI.xlsx"
df_worksheet = pd.read_excel(cmi_file, sheet_name="Worksheet", engine="openpyxl")
df_worksheet.columns = [str(c).strip() for c in df_worksheet.columns]

c_plan = _find_col(df_worksheet, ["Indicadores Plan estrategico"])
c_proyecto = _find_col(df_worksheet, ["Proyecto"])

worksheet = df_worksheet[["Id", "Indicador", "Linea", "Objetivo", c_plan, c_proyecto]].copy()
worksheet = worksheet.rename(columns={c_plan: "FlagPlanEstrategico", c_proyecto: "Proyecto"})
worksheet["Id"] = worksheet["Id"].apply(_id_limpio)
worksheet["FlagPlanEstrategico"] = pd.to_numeric(worksheet["FlagPlanEstrategico"], errors="coerce").fillna(0).astype(int)
worksheet["Proyecto"] = pd.to_numeric(worksheet["Proyecto"], errors="coerce").fillna(0).astype(int)
worksheet = worksheet[worksheet["Id"] != ""].copy()

print(f"   OK: {len(worksheet)} registros")
print(f"   FlagPlanEstrategico = 1: {(worksheet['FlagPlanEstrategico'] == 1).sum()}")
print(f"   Proyecto = 1: {(worksheet['Proyecto'] == 1).sum()}")

# PASO 2: Filtrar PDI
print("\n2. Filtrar FlagPlanEstrategico = 1...")
pdi = worksheet[worksheet["FlagPlanEstrategico"] == 1].copy()
print(f"   OK: {len(pdi)} registros")

# PASO 3: Filtrar NO-Proyectos
print("\n3. Filtrar Proyecto != 1...")
pdi = pdi[pdi["Proyecto"] != 1].copy()
print(f"   OK: {len(pdi)} registros")

if pdi.empty:
    print("\n   ERROR: PDI está vacío después de filtros!")
    print("   Esto explica por qué preparar_pdi_con_cierre() retorna vacío")
else:
    # PASO 4: Cargar Cierres
    print("\n4. Cargar Cierres (Consolidado Cierres)...")
    consolidado_file = DATA_OUTPUT / "Resultados Consolidados.xlsx"
    xl = pd.ExcelFile(consolidado_file, engine="openpyxl")
    df_cierres = xl.parse("Consolidado Cierres")
    df_cierres.columns = [str(c).strip() for c in df_cierres.columns]
    
    print(f"   OK: {len(df_cierres)} registros")
    
    # PASO 5: Verificar que hay datos de 2025
    print("\n5. Verificar datos de 2025...")
    c_anio = _find_col(df_cierres, ["Año", "Anio"])
    c_mes = _find_col(df_cierres, ["Mes"])
    
    if c_anio:
        años = pd.to_numeric(df_cierres[c_anio], errors="coerce").dropna().unique()
        print(f"   Años en Cierres: {sorted(años)}")
        data_2025 = df_cierres[pd.to_numeric(df_cierres[c_anio], errors="coerce") == 2025]
        print(f"   Registros de 2025: {len(data_2025)}")
    
    # PASO 6: Verificar intersección de IDs
    print("\n6. Verificar intersección de IDs...")
    pdi_ids = set(pdi["Id"].unique())
    cierres_ids = set(pd.Series(df_cierres[["Id"]].squeeze()).unique())
    
    print(f"   IDs en PDI: {len(pdi_ids)}")
    print(f"   IDs en Cierres: {len(cierres_ids)}")
    
    intersect = pdi_ids & cierres_ids
    print(f"   IDs en ambos: {len(intersect)}")
    
    if len(intersect) == 0:
        print("\n   ERROR: NO hay IDs en común!")
        print("   Esto explica por qué el merge en preparar_pdi_con_cierre() retorna vacío")
    else:
        print(f"\n   OK: Hay {len(intersect)} IDs en común (suficiente para continuar)")

print("\n" + "="*80)
