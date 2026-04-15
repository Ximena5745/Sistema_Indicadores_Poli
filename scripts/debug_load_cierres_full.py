#!/usr/bin/env python3
"""Debug load_cierres paso a paso."""

import sys
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.config import DATA_OUTPUT

print("\n" + "="*80)
print("DEBUG: load_cierres() paso a paso")
print("="*80)

OUT_XLSX = DATA_OUTPUT / "Resultados Consolidados.xlsx"

print(f"\nArchivo: {OUT_XLSX}")
print(f"Existe: {OUT_XLSX.exists()}")

# Paso 1: Abrir archivo
print("\n1. Abrir ExcelFile...")
try:
    xl = pd.ExcelFile(OUT_XLSX, engine="openpyxl")
    print(f"   OK: {len(xl.sheet_names)} hojas")
    print(f"   Hojas: {xl.sheet_names}")
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# Paso 2: Seleccionar hoja
sheet = "Cierre historico" if "Cierre historico" in xl.sheet_names else (
    "Consolidado Cierres" if "Consolidado Cierres" in xl.sheet_names else None
)
print(f"\n2. Seleccionar hoja...")
print(f"   sheet: {sheet}")

if not sheet:
    print("   ERROR: No hoja encontrada")
    exit(1)

# Paso 3: Parsear
print(f"\n3. Parsear hoja '{sheet}'...")
try:
    df = xl.parse(sheet)
    print(f"   OK: {len(df)} filas x {len(df.columns)} columnas")
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# Paso 4: Normalizar columnas
print(f"\n4. Normalizar columnas...")
df.columns = [str(c).strip() for c in df.columns]
print(f"   Todas las columnas ({len(df.columns)}):")
for i, col in enumerate(df.columns, 1):
    print(f"     {i:2d}. {col}")

# Paso 5: Buscar columnas necesarias
print(f"\n5. Buscar columnas...")

def _norm_text(value: str) -> str:
    import unicodedata
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

def _id_limpio(x) -> str:
    if pd.isna(x):
        return ""
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x).strip()

def _find_col(df: pd.DataFrame, names: list[str]) -> str | None:
    lookup = {_norm_text(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(_norm_text(name))
        if hit:
            return hit
    return None

c_id = _find_col(df, ["Id", "ID"])
c_ind = _find_col(df, ["Indicador"])
c_fecha = _find_col(df, ["Fecha"])
c_anio = _find_col(df, ["Año", "Anio"])
c_mes = _find_col(df, ["Mes"])
c_meta = _find_col(df, ["Meta"])
c_ejec = _find_col(df, ["Ejecucion", "Ejecución"])
c_sentido = _find_col(df, ["Sentido"])

print(f"   c_id: {c_id}")
print(f"   c_ind: {c_ind}")
print(f"   c_fecha: {c_fecha}")
print(f"   c_anio: {c_anio}")
print(f"   c_mes: {c_mes}")
print(f"   c_meta: {c_meta}")
print(f"   c_ejec: {c_ejec}")
print(f"   c_sentido: {c_sentido}")

if not c_id:
    print(f"   ERROR: c_id es None")
    exit(1)

# Paso 6: Construir output
print(f"\n6. Construir output...")
out = pd.DataFrame()
out["Id"] = df[c_id].apply(_id_limpio)
print(f"   Agregado: Id ({len(out[out['Id'] != ''])} no-vacíos)")

if c_ind:
    out["Indicador"] = df[c_ind].astype(str).str.strip()
if c_fecha:
    out["Fecha"] = pd.to_datetime(df[c_fecha], errors="coerce")
if c_anio:
    out["Anio"] = pd.to_numeric(df[c_anio], errors="coerce")
if c_mes:
    out["Mes"] = pd.to_numeric(df[c_mes], errors="coerce")
if c_meta:
    out["Meta"] = pd.to_numeric(df[c_meta], errors="coerce")
if c_ejec:
    out["Ejecucion"] = pd.to_numeric(df[c_ejec], errors="coerce")
if c_sentido:
    out["Sentido"] = df[c_sentido].astype(str).str.strip()

print(f"   OK: {len(out)} filas con {len(out.columns)} columnas")

# Paso 7: Filtrar IDs no-vacíos
print(f"\n7. Filtrar IDs no-vacíos...")
pre = len(out)
out = out[out["Id"] != ""].copy()
print(f"   Pre: {pre}, Post: {len(out)}")

if out.empty:
    print(f"   ERROR: output está vacío después de filtro!")

# Paso 8: Calcular cumplimiento
print(f"\n8. Calcular cumplimiento...")
if "Meta" in out.columns and "Ejecucion" in out.columns:
    meta_n = out["Meta"]
    ejec_n = out["Ejecucion"]
    print(f"   Meta: {meta_n.notna().sum()} no-nulos")
    print(f"   Ejecucion: {ejec_n.notna().sum()} no-nulos")
    
    out["cumplimiento_pct"] = pd.NA

print(f"\n9. RESULTADO FINAL:")
print(f"   Filas: {len(out)}")
print(f"   Columnas: {list(out.columns)}")
if not out.empty and len(out) <= 10:
    print(f"\n   Datos:")
    print(out)
elif not out.empty:
    print(f"\n   Primeros 5:")
    print(out.head())

print("\n" + "="*80)
