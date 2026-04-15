#!/usr/bin/env python3
"""Investigar por qué no hay IDs en común."""

import sys
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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

print("\n" + "="*80)
print("INVESTIGAR: Por qué no hay IDs en común")
print("="*80)

# Cargar PDI
print("\n1. PDI IDs...")
cmi_file = DATA_RAW / "Indicadores por CMI.xlsx"
df_worksheet = pd.read_excel(cmi_file, sheet_name="Worksheet", engine="openpyxl")
df_worksheet.columns = [str(c).strip() for c in df_worksheet.columns]

worksheet = df_worksheet[["Id"]].copy()
worksheet["Id_raw"] = worksheet["Id"]
worksheet["Id"] = worksheet["Id"].apply(_id_limpio)
worksheet["FlagPlanEstrategico"] = pd.to_numeric(df_worksheet["Indicadores Plan estrategico"], errors="coerce").fillna(0).astype(int)
worksheet["Proyecto"] = pd.to_numeric(df_worksheet["Proyecto"], errors="coerce").fillna(0).astype(int)

pdi = worksheet[(worksheet["FlagPlanEstrategico"] == 1) & (worksheet["Proyecto"] != 1)]
pdi_ids = set(pdi["Id"].unique())

print(f"   IDs PDI ({len(pdi_ids)} únicos):")
pdi_list = sorted(list(pdi_ids))[:10]
for id in pdi_list:
    print(f"     {repr(id)}")
if len(pdi_list) < len(pdi_ids):
    print(f"     ... y {len(pdi_ids) - len(pdi_list)} más")

# Cargar Cierres
print("\n2. Cierres IDs...")
consolidado_file = DATA_OUTPUT / "Resultados Consolidados.xlsx"
df_cierres = pd.read_excel(consolidado_file, sheet_name="Consolidado Cierres", engine="openpyxl")
df_cierres.columns = [str(c).strip() for c in df_cierres.columns]

cierres = df_cierres[["Id"]].copy()
cierres["Id_raw"] = cierres["Id"]
cierres["Id"] = cierres["Id"].apply(_id_limpio)

cierres_ids = set(cierres["Id"].unique())

print(f"   IDs Cierres ({len(cierres_ids)} únicos):")
cierres_list = sorted(list(cierres_ids))[:10]
for id in cierres_list:
    print(f"     {repr(id)}")
if len(cierres_list) < len(cierres_ids):
    print(f"     ... y {len(cierres_ids) - len(cierres_list)} más")

# Comparar
print("\n3. Comparación...")
intersect = pdi_ids & cierres_ids
print(f"   Intersección: {len(intersect)}")

# Ejemplo: verificar si alguns IDs de PDI están en Cierres
if pdi_ids:
    sample_pdi_id = list(pdi_ids)[0]
    print(f"\n4. Verificar ID de ejemplo PDI: {repr(sample_pdi_id)}")
    print(f"   ¿Está en Cierres? {sample_pdi_id in cierres_ids}")
    
    # Buscar similar
    similar = [c for c in cierres_ids if str(c)[:3] == str(sample_pdi_id)[:3]]
    if similar:
        print(f"   IDs similares en Cierres: {similar}")

# Diferencias
print("\n5. IDs solo en PDI (no en Cierres):")
only_pdi = pdi_ids - cierres_ids
print(f"   Cantidad: {len(only_pdi)}")
if len(only_pdi) <= 10:
    for id in sorted(only_pdi):
        print(f"     {repr(id)}")
else:
    for id in sorted(list(only_pdi)[:5]):
        print(f"     {repr(id)}")
    print(f"     .. y {len(only_pdi) - 5} más")

print("\n6. IDs solo en Cierres (no en PDI):")
only_cierres = cierres_ids - pdi_ids
print(f"   Cantidad: {len(only_cierres)}")
if len(only_cierres) <= 10:
    for id in sorted(only_cierres):
        print(f"     {repr(id)}")
else:
    for id in sorted(list(only_cierres)[:5]):
        print(f"     {repr(id)}")
    print(f"     .. y {len(only_cierres) - 5} más")

# Revisar si hay problemas de tipo
print("\n7. Revisión de tipos:")
print(f"   PDI IDs (muestra): types = {[type(id).__name__ for id in list(pdi_ids)[:3]]}")
print(f"   Cierres IDs (muestra): types = {[type(id).__name__ for id in list(cierres_ids)[:3]]}")

print("\n" + "="*80)
