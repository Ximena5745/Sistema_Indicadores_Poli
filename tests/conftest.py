"""
tests/conftest.py — Configuración global de pytest y fixtures compartidas

Propósito:
- Fixtures dinámicas para cargar IDs (Plan Anual, Proyectos, etc.)
- Pre-condiciones que validan data correctamente cargada
- Evitar hardcodeo de IDs en tests (mantener robustez)

Principio Clave: Todos los IDs de test se cargan dinámicamente desde config/sources,
NUNCA hardcodeados. Esto asegura que tests sigan siendo válidos cuando datos cambian.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import IDS_PLAN_ANUAL
from core.semantica import CategoriaCumplimiento


# ============================================================================
# CONFIGURACIÓN DE PYTEST
# ============================================================================

# Excluir scripts de diagnóstico que no son tests pytest reales
collect_ignore_glob = [
    "test_consol.py",
    "test_filter.py",
    "test_sunburst.py",
    "archived/**/*.py",
]


# ============================================================================
# PRE-CONDITION FIXTURES: Validar que data está correctamente cargada
# ============================================================================


@pytest.fixture(scope="session")
def validate_plan_anual_ids_loaded():
    """
    Pre-condición: Asegurar que IDS_PLAN_ANUAL está cargado desde Excel.
    
    Valida que la configuración fue inicializada con IDs Plan Anual reales
    desde data/raw/Indicadores por CMI.xlsx
    
    Si esto falla, TODOS los tests Plan Anual deben ser skippeados.
    """
    if len(IDS_PLAN_ANUAL) == 0:
        pytest.skip(
            "⚠️  IDS_PLAN_ANUAL vacío. "
            "Verificar que data/raw/Indicadores por CMI.xlsx esté cargado."
        )
    
    # Verificar que todos los IDs son strings
    for id_val in IDS_PLAN_ANUAL:
        if not isinstance(id_val, str):
            raise TypeError(
                f"Plan Anual ID debe ser string, obtuvo {type(id_val)}: {id_val}"
            )
    
    # Verificar cantidad razonable (esperado ~100-110 en institución)
    if len(IDS_PLAN_ANUAL) < 50:
        pytest.warns(
            UserWarning,
            f"⚠️  Solo {len(IDS_PLAN_ANUAL)} IDs Plan Anual cargados. "
            "Esperado ~100+. Verificar fuente Excel."
        )
    
    return IDS_PLAN_ANUAL


# ============================================================================
# FIXTURES DE IDS DINÁMICOS: Obtener IDs reales de config, NO hardcodeados
# ============================================================================


@pytest.fixture
def plan_anual_id(validate_plan_anual_ids_loaded):
    """
    Obtener CUALQUIER ID Plan Anual de configuración actual.
    
    ✅ Dinámico: Carga desde IDS_PLAN_ANUAL en tiempo de test
    ✅ Robusto: Funciona incluso si IDs específicos cambian
    ✅ Válido: Garantizado ser ID Plan Anual real
    
    Uso:
        def test_algo(plan_anual_id):
            categoria = categorizar_cumplimiento(0.92, id_indicador=plan_anual_id)
    
    Ejemplo:
        Si IDS_PLAN_ANUAL = {'1', '10', '373'}, retorna '1'
        Si IDS_PLAN_ANUAL = {'10', '373'} (luego '1' eliminado), retorna '10'
        Siempre retorna un ID Plan Anual válido
    """
    return next(iter(validate_plan_anual_ids_loaded))


@pytest.fixture
def all_plan_anual_ids(validate_plan_anual_ids_loaded):
    """
    Obtener TODOS los IDs Plan Anual de configuración.
    
    Útil para tests parametrizados que validan comportamiento en TODOS los IDs.
    
    Uso:
        @pytest.mark.parametrize("id_pa", all_plan_anual_ids())
        def test_todos_pa(id_pa):
            ...
    """
    return list(validate_plan_anual_ids_loaded)


@pytest.fixture
def regular_indicator_id():
    """
    Obtener ID indicador regular (NO Plan Anual) para testing.
    
    ⚠️  NOTA: Usa ID estático fuera del conjunto conocido Plan Anual.
    Si datos institucionales incluyen ID='999', actualizar este fixture.
    
    Retorna: string ID garantizado NO estar en IDS_PLAN_ANUAL
    """
    candidate = "999"
    if candidate in IDS_PLAN_ANUAL:
        for i in range(10000, 10100):
            candidate = str(i)
            if candidate not in IDS_PLAN_ANUAL:
                break
    return candidate


# ============================================================================
# HELPERS DE PARAMETRIZACIÓN: Para descubrimiento de tests
# ============================================================================


def get_plan_anual_ids():
    """
    Helper para obtener IDs Plan Anual para pytest.mark.parametrize.
    
    Uso:
        @pytest.mark.parametrize("plan_anual_id", get_plan_anual_ids())
        def test_todos_plan_anual(plan_anual_id):
            ...
    
    Retorna: Lista de IDs Plan Anual, o lista vacía si no cargó
    """
    if len(IDS_PLAN_ANUAL) == 0:
        return []
    return sorted(list(IDS_PLAN_ANUAL))


# ============================================================================
# FIXTURES DE MOCK DATA: Para unit tests aislados
# ============================================================================


@pytest.fixture
def sample_cumplimiento_values():
    """Valores de cumplimiento de muestra para testing de categorización"""
    return {
        "peligro": 0.75,  # < 0.80
        "peligro_boundary": 0.799,
        "alerta": 0.92,  # 0.80 - 0.99
        "alerta_boundary_upper": 0.999,
        "cumplimiento": 1.00,  # 1.00 - 1.04
        "cumplimiento_boundary_upper": 1.049,
        "sobrecumplimiento": 1.12,  # >= 1.05
        "zero": 0.0,
        "very_high": 3.0,
    }


@pytest.fixture
def sample_plan_anual_values():
    """Valores de cumplimiento específicos para umbrales Plan Anual"""
    return {
        "peligro_pa": 0.90,  # < 0.95 (umbral Plan Anual)
        "alerta_pa": 0.94,  # 0.80 - 0.94
        "cumplimiento_pa": 0.97,  # 0.95 - 1.00
        "sobrecumplimiento_pa": 1.10,  # > 1.00 (capped)
    }


# ============================================================================
# HELPERS DE ENUM: Normalizar comparaciones de categoría
# ============================================================================


@pytest.fixture
def categoria_enum():
    """Proporcionar acceso fácil a enum CategoriaCumplimiento en tests"""
    return CategoriaCumplimiento
