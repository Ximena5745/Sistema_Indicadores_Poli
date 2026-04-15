#!/usr/bin/env python3
"""
Debug script para diagnosticar por qué Resumen General no muestra datos.
Valida la cadena de carga de datos de inicio a fin.
"""

import sys
from pathlib import Path
import pandas as pd

# Setup paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.strategic_indicators import (
    load_worksheet_flags,
    load_pdi_catalog,
    load_cierres,
    preparar_pdi_con_cierre,
)
from core.config import DATA_RAW, DATA_OUTPUT


def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def validate_files_exist():
    """Verifica que archivos fuente existan."""
    print_section("1. VALIDACIÓN DE ARCHIVOS")
    
    files_to_check = [
        ("CMI Indicadores", DATA_RAW / "Indicadores por CMI.xlsx"),
        ("Consolidado Salida", DATA_OUTPUT / "Resultados Consolidados.xlsx"),
    ]
    
    for name, path in files_to_check:
        exists = path.exists()
        status = "✅ EXISTE" if exists else "❌ FALTA"
        print(f"{status}: {name}")
        print(f"       {path}\n")
        if not exists:
            return False
    return True


def validate_worksheet_flags():
    """Valida carga de flags del Worksheet."""
    print_section("2. VALIDACIÓN: WORKSHEET FLAGS (Indicadores por CMI.xlsx)")
    
    df = load_worksheet_flags()
    print(f"   Registros cargados: {len(df)}")
    
    if df.empty:
        print("   ❌ NO SE CARGARON REGISTROS - Problema crítico")
        return False
    
    # Columnas esperadas
    expected_cols = ["Id", "Indicador", "Linea", "Objetivo", "FlagPlanEstrategico"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        print(f"   ⚠️  Columnas faltantes: {missing}")
    
    # Estadísticas de flags
    print("\n   Distribución de FlagPlanEstrategico:")
    if "FlagPlanEstrategico" in df.columns:
        print(f"     Total = 1 (Plan Estratégico): {(df['FlagPlanEstrategico'] == 1).sum()}")
        print(f"     Total = 0: {(df['FlagPlanEstrategico'] == 0).sum()}")
    
    print("\n   Proyectos:")
    if "Proyecto" in df.columns:
        print(f"     Proyecto = 1: {(df['Proyecto'] == 1).sum()}")
        print(f"     Proyecto = 0 o NaN: {(df['Proyecto'] != 1).sum()}")
    
    # Muestreo
    plan = df[df["FlagPlanEstrategico"] == 1]
    print(f"\n   Indicadores Plan Estratégico = 1: {len(plan)}")
    if not plan.empty and len(plan) <= 5:
        print("\n   Primeros registros:")
        print(plan[["Id", "Indicador", "Linea", "Objetivo"]].to_string())
    elif not plan.empty:
        print("\n   Primeros 5 registros:")
        print(plan.head()[["Id", "Indicador", "Linea", "Objetivo"]].to_string())
    
    return not plan.empty


def validate_pdi_catalog():
    """Valida catálogo PDI."""
    print_section("3. VALIDACIÓN: CATÁLOGO PDI")
    
    df = load_pdi_catalog()
    print(f"   Registros: {len(df)}")
    
    if df.empty:
        print("   ⚠️  Catálogo vacío - pero esto puede ser OK si Linea/Objetivo vienen del Worksheet")
        return True
    
    print(f"   Líneas estratégicas: {df['Linea'].nunique()}")
    print(f"   Objetivos estratégicos: {df['Objetivo'].nunique()}")
    
    if len(df) <= 10:
        print("\n   Catálogo completo:")
        print(df.to_string())
    else:
        print("\n   Primeros registros:")
        print(df.head().to_string())
    
    return True


def validate_cierres():
    """Valida carga de cierres."""
    print_section("4. VALIDACIÓN: CIERRES (Resultados Consolidados.xlsx)")
    
    df = load_cierres()
    print(f"   Registros cargados: {len(df)}")
    
    if df.empty:
        print("   ❌ NO SE CARGARON CIERRES - Problema crítico")
        return False
    
    # Columnas clave
    expected = ["Id", "Indicador", "Anio", "Mes", "cumplimiento_pct", "Nivel de cumplimiento"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        print(f"   ⚠️  Columnas faltantes: {missing}")
    
    # Análisis temporal
    if "Anio" in df.columns:
        print(f"\n   Años disponibles: {sorted(df['Anio'].dropna().unique())}")
    
    if "Mes" in df.columns:
        print(f"   Meses disponibles (muestra): {sorted(df['Mes'].dropna().unique())[:12]}")
    
    # Datos de cumplimiento
    if "cumplimiento_pct" in df.columns:
        valid_cumpl = df["cumplimiento_pct"].notna().sum()
        print(f"\n   Registros con cumplimiento_pct: {valid_cumpl}/{len(df)} ({100*valid_cumpl/len(df):.1f}%)")
        print(f"   Min/Max cumplimiento_pct: {df['cumplimiento_pct'].min():.1f}% / {df['cumplimiento_pct'].max():.1f}%")
    
    # Muestreo
    if len(df) <= 10:
        print("\n   Datos de cierre:")
        cols_show = [c for c in ["Id", "Indicador", "Anio", "Mes", "cumplimiento_pct"] if c in df.columns]
        print(df[cols_show].to_string())
    else:
        print(f"\n   Primeros 5 registros:")
        cols_show = [c for c in ["Id", "Indicador", "Anio", "Mes", "cumplimiento_pct"] if c in df.columns]
        print(df[cols_show].head().to_string())
    
    return True


def validate_preparar_pdi_2025():
    """Valida función completa para 2025."""
    print_section("5. VALIDACIÓN: PREPARAR PDI CON CIERRE (2025 - Diciembre)")
    
    result = preparar_pdi_con_cierre(2025, 12)
    print(f"   Registros resultantes: {len(result)}")
    
    if result.empty:
        print("   ❌ RESULTADO VACÍO - Este es el problema")
        print("\n   Investigando causas...")
        
        # Debug: verificar paso a paso
        flags = load_worksheet_flags()
        plan = flags[flags["FlagPlanEstrategico"] == 1]
        print(f"     → Indicadores con FlagPlanEstrategico=1: {len(plan)}")
        
        if "Proyecto" in plan.columns:
            plan_no_proj = plan[plan["Proyecto"] != 1]
            print(f"     → Después de filtrar Proyecto≠1: {len(plan_no_proj)}")
        
        cierres = load_cierres()
        from services.strategic_indicators import cierre_por_corte
        cierre_filt = cierre_por_corte(cierres, 2025, 12)
        print(f"     → Cierres filtrados a corte 2025-12: {len(cierre_filt)}")
        
        # Encuentra IDs en común
        ids_plan = set(plan["Id"].unique())
        ids_cierre = set(cierre_filt["Id"].unique())
        ids_intersect = ids_plan & ids_cierre
        print(f"     → IDs en Plan: {len(ids_plan)}")
        print(f"     → IDs en Cierres: {len(ids_cierre)}")
        print(f"     → IDs en ambos: {len(ids_intersect)}")
        
        if len(ids_intersect) > 0 and len(ids_intersect) <= 3:
            print(f"     → IDs intersectados: {ids_intersect}")
        
        return False
    
    # Estadísticas
    print(f"\n   Líneas estratégicas: {result['Linea'].nunique()}")
    print(f"   Objetivos estratégicos: {result['Objetivo'].nunique()}")
    
    if "cumplimiento_pct" in result.columns:
        valid = result["cumplimiento_pct"].notna().sum()
        print(f"   Con cumplimiento_pct: {valid}/{len(result)}")
    
    if "Nivel de cumplimiento" in result.columns:
        print(f"\n   Distribución por nivel:")
        print(result["Nivel de cumplimiento"].value_counts().to_string())
    
    if len(result) <= 10:
        print("\n   Datos completos:")
        cols = [c for c in ["Id", "Indicador", "Linea", "Objetivo", "cumplimiento_pct"] if c in result.columns]
        print(result[cols].to_string())
    else:
        print(f"\n   Primeros 5 registros:")
        cols = [c for c in ["Id", "Indicador", "Linea", "Objetivo", "cumplimiento_pct"] if c in result.columns]
        print(result[cols].head().to_string())
    
    return True


def main():
    """Ejecuta todas las validaciones."""
    print("\n" + "="*80)
    print("  DIAGNÓSTICO: RESUMEN GENERAL - NO MUESTRA DATOS")
    print("="*80)
    
    steps = [
        ("Archivos", validate_files_exist),
        ("Worksheet Flags", validate_worksheet_flags),
        ("PDI Catalog", validate_pdi_catalog),
        ("Cierres", validate_cierres),
        ("Preparar PDI 2025", validate_preparar_pdi_2025),
    ]
    
    status = {}
    for name, func in steps:
        try:
            ok = func()
            status[name] = "✅ OK" if ok else "⚠️  FALLA"
        except Exception as e:
            print(f"\n   ❌ EXCEPCIÓN: {e}")
            import traceback
            traceback.print_exc()
            status[name] = "❌ ERROR"
    
    # Resumen final
    print_section("RESUMEN")
    for name, result in status.items():
        print(f"   {result} → {name}")
    
    # Recomendaciones
    print_section("RECOMENDACIONES")
    if status.get("Preparar PDI 2025") == "✅ OK":
        print("   ✅ Los datos se cargan correctamente.")
        print("   → Problema probablemente en la interfaz (streamlit_app)")
    else:
        print("   ❌ Los datos NO se cargan correctamente.")
        print("   → Revisar los pasos que marcaron falla arriba")


if __name__ == "__main__":
    main()
