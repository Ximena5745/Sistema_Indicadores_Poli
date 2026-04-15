#!/usr/bin/env python3
"""Debug load_worksheet_flags - ejecución completa."""

import sys
import traceback
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

print("\n" + "="*80)
print("DEBUG: Ejecutar load_worksheet_flags()")
print("="*80)

try:
    from services.strategic_indicators import load_worksheet_flags
    
    print("\nLlamando a load_worksheet_flags()...")
    result = load_worksheet_flags()
    
    print(f"Resultado: {len(result)} filas x {len(result.columns)} columnas")
    if result.empty:
        print("VACIO!")
    else:
        print(f"Columnas: {list(result.columns)}")
        print("\nPrimeros registros:")
        print(result.head())
        
except Exception as e:
    print(f"EXCEPCION: {e}")
    traceback.print_exc()

# Ahora intenta line-by-line
print("\n\n" + "="*80)
print("DEBUG: Paso a paso (copia del código)")
print("="*80)

from core.config import DATA_RAW, CACHE_TTL
import unicodedata

RAW_XLSX = DATA_RAW / "Indicadores por CMI.xlsx"

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

print(f"\n1. Leyendo archivo: {RAW_XLSX}")
if not RAW_XLSX.exists():
    print("   NO EXISTE")
else:
    df = pd.read_excel(RAW_XLSX, sheet_name="Worksheet", engine="openpyxl")
    print(f"   OK: {len(df)} filas")
    
    df.columns = [str(c).strip() for c in df.columns]
    
    print("\n2. Buscando columnas...")
    c_id = _find_col(df, ["Id", "ID"])
    print(f"   c_id: {c_id}")
    c_ind = _find_col(df, ["Indicador"])
    print(f"   c_ind: {c_ind}")
    c_linea = _find_col(df, ["Linea"])
    print(f"   c_linea: {c_linea}")
    c_obj = _find_col(df, ["Objetivo"])
    print(f"   c_obj: {c_obj}")
    c_factor = _find_col(df, ["FACTOR", "Factor"])
    print(f"   c_factor: {c_factor}")
    c_car = _find_col(df, ["CARACTERISTICA", "Caracteristica", "CARACTERÍSTICA"])
    print(f"   c_car: {c_car}")
    c_plan = _find_col(df, ["Indicadores Plan estrategico"])
    print(f"   c_plan: {c_plan}")
    c_cna = _find_col(df, ["CNA"])
    print(f"   c_cna: {c_cna}")
    c_proyecto = _find_col(df, ["Proyecto", "PROYECTO"])
    print(f"   c_proyecto: {c_proyecto}")
    
    print("\n3. Verificar 'needed'...")
    needed = [c for c in [c_id, c_ind, c_linea, c_obj, c_factor, c_car, c_plan, c_cna] if c]
    print(f"   needed: {needed} ({len(needed)} columnas)")
    
    if not needed:
        print("   ERROR: needed está vacío!")
    else:
        print("\n4. Seleccionar columnas...")
        out = df[needed].copy()
        print(f"   out: {len(out)} filas x {len(out.columns)} columnas")
        
        print("\n5. Renombrar...")
        rename_map = {
            c_id: "Id",
            c_ind: "Indicador",
            c_linea: "Linea",
            c_obj: "Objetivo",
            c_factor: "Factor",
            c_car: "Caracteristica",
            c_plan: "FlagPlanEstrategico",
            c_cna: "FlagCNA",
        }
        if c_proyecto:
            out = df[needed + [c_proyecto]].copy()
            rename_map[c_proyecto] = "Proyecto"
            print(f"   Agregado c_proyecto: {c_proyecto}")
        
        out = out.rename(columns={k: v for k, v in rename_map.items() if k is not None})
        print(f"   Columnas después rename: {list(out.columns)}")
        
        print("\n6. Validar ID...")
        if "Id" not in out.columns:
            print("   ERROR: 'Id' no está en out!")
        else:
            out["Id"] = out["Id"].apply(_id_limpio)
            print(f"   OK: IDs limpiados")
            
            print("\n7. Procesar flags...")
            for flag in ["FlagPlanEstrategico", "FlagCNA"]:
                if flag in out.columns:
                    print(f"   Procesando {flag}...")
                    print(f"     Valores antes: {out[flag].unique()}")
                    out[flag] = pd.to_numeric(out[flag], errors="coerce").fillna(0).astype(int)
                    print(f"     Valores después: {out[flag].unique()}")
                else:
                    print(f"   Columna {flag} no existe, asignando 0")
                    out[flag] = 0
            
            print("\n8. Procesar Proyecto...")
            if "Proyecto" in out.columns:
                out["Proyecto"] = pd.to_numeric(out["Proyecto"], errors="coerce").fillna(0).astype(int)
                print(f"   OK: {out['Proyecto'].unique()}")
            
            print("\n9. Filtrar IDs vacíos...")
            pre_filter = len(out)
            out = out[out["Id"] != ""].copy()
            print(f"   Pre-filtro: {pre_filter}, Post-filtro: {len(out)}")
            
            print("\n10. Deduplicar...")
            pre_dedup = len(out)
            out = out.drop_duplicates(subset=["Id"], keep="first").reset_index(drop=True)
            print(f"   Pre-dedup: {pre_dedup}, Post-dedup: {len(out)}")
            
            print(f"\nFINAL: {len(out)} registros")
            if not out.empty:
                print("Primeros registros:")
                print(out.head())

print("\n" + "="*80)
