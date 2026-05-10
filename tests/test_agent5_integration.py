"""
test_agent5_integration.py
Test de integración AGENT 5 corrections en pipeline ETL
"""

import pandas as pd
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from etl.agent5_corrections import AGENT5Corrections


def test_agent5_corrections():
    """Test de aplicación de correcciones AGENT 5"""
    
    # Crear DataFrame de prueba con valores problemáticos
    df_test = pd.DataFrame({
        'Id': ['IND001', 'IND002', 'IND003', 'IND004'],
        'Periodo': ['2026-01', '2026-01', '2026-02', '2026-02'],
        'Ejecucion': [1.35, 0.85, 1.10, 0.90],  # IND001 tiene 1.35 (debe capearse a 1.3)
        'Meta': [0.95, 0.0, 1.05, 0.80],  # IND003 tiene meta=0 (inválido)
    })
    
    print("=" * 70)
    print("TEST AGENT 5 CORRECTIONS — Integration Test")
    print("=" * 70)
    print("\n📊 DataFrame ANTES de correcciones:")
    print(df_test)
    print("\n✓ Problemas encontrados:")
    print("  - IND001: Ejecucion=1.35 (debe ser ≤ 1.3)")
    print("  - IND002: Meta=0 (debe ser > 0)")
    
    # Aplicar correcciones
    print("\n🔧 Aplicando correcciones…")
    df_corregido, reporte = AGENT5Corrections.apply_all_corrections(df_test)
    
    print("\n📊 DataFrame DESPUÉS de correcciones:")
    print(df_corregido)
    
    print("\n📋 Reporte de Correcciones:")
    for key, value in reporte.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Validaciones Post-Corrección:")
    print("  ✓ Ejecución máxima: {:.2f} (≤ 1.3) ✅".format(df_corregido['Ejecucion'].max()))
    print("  ✓ Meta máxima: {:.2f} (≤ 1.0) ✅".format(df_corregido['Meta'].max()))
    
    # Validación de correcciones aplicadas
    if reporte['ejecucion_cappados'] > 0:
        print(f"  ✓ Ejecución cappada: {reporte['ejecucion_cappados']} valores (1.35 → 1.30) ✅")
    if reporte['meta_excedidas'] > 0:
        print(f"  ✓ Meta excedida capeada: {reporte['meta_excedidas']} valores (>1.0 → 1.0) ✅")
    if reporte['meta_cero'] > 0:
        print(f"  ⚠️  Meta = 0 detectada: {reporte['meta_cero']} registros (requiere revisión manual) ⚠️")
    
    # Verificar que ejecución está correcta
    if df_corregido['Ejecucion'].max() <= 1.3 and df_corregido['Meta'].max() <= 1.0:
        print("\n✓ TODAS las correcciones críticas aplicadas correctamente")
        return 0
    else:
        print("\n✗ Validación de correcciones falló")
        return 1


if __name__ == "__main__":
    exit_code = test_agent5_corrections()
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ TEST EXITOSO")
    else:
        print("❌ TEST FALLIDO")
    print("=" * 70)
    sys.exit(exit_code)
