"""
scripts/agent2_etl_pipeline_audit.py (Versión Simplificada)
AGENT 2 — ETL & Pipeline Analysis
Auditoría de reproducibilidad, modularidad y validación del ETL
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ETLPipelineAudit:
    """Auditoría de architecture del pipeline ETL SGIND"""

    def __init__(self, root_path: Path | None = None):
        self.root = Path(root_path) if root_path else Path(__file__).parent.parent
        self.scripts_path = self.root / "scripts"
        self.etl_path = self.root / "scripts" / "etl"
        self.hallazgos: List[Dict[str, Any]] = []

    def audit_all(self) -> Dict[str, Any]:
        """Ejecutar auditoría completa de 8 dimensiones"""
        logger.info("=" * 70)
        logger.info("AGENT 2 — ETL Pipeline Audit")
        logger.info("=" * 70)

        results = {
            "timestamp": datetime.now().isoformat(),
            "framework": "SGIND v1.0",
            "dimensiones": {},
        }

        # Dimensión 1: Separación de Responsabilidades
        logger.info("\n📋 Dimensión 1: Separación de Responsabilidades")
        results["dimensiones"]["separation_of_concerns"] = self._audit_separation()

        # Dimensión 2: Reproducibilidad
        logger.info("\n📋 Dimensión 2: Reproducibilidad")
        results["dimensiones"]["reproducibility"] = self._audit_reproducibility()

        # Dimensión 3: Contratos de Datos
        logger.info("\n📋 Dimensión 3: Contratos de Datos")
        results["dimensiones"]["data_contracts"] = self._audit_data_contracts()

        # Dimensión 4: Flujo de Datos
        logger.info("\n📋 Dimensión 4: Flujo de Datos")
        results["dimensiones"]["data_flow"] = self._audit_data_flow()

        # Dimensión 5: Versionado
        logger.info("\n📋 Dimensión 5: Versionado")
        results["dimensiones"]["versioning"] = self._audit_versioning()

        # Dimensión 6: Manejo de Errores
        logger.info("\n📋 Dimensión 6: Manejo de Errores")
        results["dimensiones"]["error_handling"] = self._audit_error_handling()

        # Dimensión 7: Modularidad
        logger.info("\n📋 Dimensión 7: Modularidad")
        results["dimensiones"]["modularity"] = self._audit_modularity()

        # Dimensión 8: Configuración
        logger.info("\n📋 Dimensión 8: Configuración")
        results["dimensiones"]["configuration"] = self._audit_configuration()

        results["hallazgos"] = self.hallazgos
        results["summary"] = {
            "total_hallazgos": len(self.hallazgos),
            "criticos": len([h for h in self.hallazgos if h.get("priority") == "CRITICO"]),
            "altos": len([h for h in self.hallazgos if h.get("priority") == "ALTO"]),
        }

        return results

    def _audit_separation(self) -> Dict[str, Any]:
        """Dimensión 1: Separación de Responsabilidades"""
        result = {"status": "OK"}

        consolidar = self.scripts_path / "consolidar_api.py"
        actualizar = self.scripts_path / "actualizar_consolidado.py"

        if not consolidar.exists():
            result["status"] = "ERROR"
            self.hallazgos.append({
                "dimensión": "Separación",
                "hallazgo": "consolidar_api.py no encontrado",
                "priority": "CRITICO",
            })

        if not actualizar.exists():
            result["status"] = "ERROR"
            self.hallazgos.append({
                "dimensión": "Separación",
                "hallazgo": "actualizar_consolidado.py no encontrado",
                "priority": "CRITICO",
            })

        etl_files = list(self.etl_path.glob("*.py"))
        result["etl_modules_count"] = len(etl_files)

        if len(etl_files) < 5:
            result["status"] = "WARNING"
            self.hallazgos.append({
                "dimensión": "Separación",
                "hallazgo": f"Pocos módulos ETL ({len(etl_files)} < 5)",
                "recomendación": "Extraer funciones a módulos reutilizables",
                "priority": "MEDIO",
            })

        logger.info(f"   Status: {result['status']}")
        return result

    def _audit_reproducibility(self) -> Dict[str, Any]:
        """Dimensión 2: Reproducibilidad"""
        result = {"status": "OK", "checks": {}}

        actualizar = self.scripts_path / "actualizar_consolidado.py"
        if actualizar.exists():
            try:
                content = actualizar.read_text(encoding="utf-8", errors="ignore")
                result["checks"]["has_deduplication"] = "deduplicar" in content or "drop_duplicates" in content
                result["checks"]["hardcoded_year"] = "2025" in content or "2026" in content
                result["checks"]["hardcoded_paths"] = "data/output" in content or "data/raw" in content

                if result["checks"]["hardcoded_year"]:
                    result["status"] = "WARNING"
                    self.hallazgos.append({
                        "dimensión": "Reproducibilidad",
                        "hallazgo": "Años hardcodeados en código",
                        "recomendación": "Parametrizar AÑO_CIERRE_ACTUAL en config",
                        "priority": "ALTO",
                    })
            except Exception as e:
                logger.warning(f"Error leyendo archivo: {e}")

        logger.info(f"   Status: {result['status']}")
        return result

    def _audit_data_contracts(self) -> Dict[str, Any]:
        """Dimensión 3: Contratos de Datos"""
        result = {"status": "OK", "great_expectations": False, "validation_gate_found": False}

        artifacts = self.root / "artifacts"
        if artifacts.exists():
            ge_files = list(artifacts.glob("*GREAT_EXPECTATIONS*"))
            result["great_expectations"] = len(ge_files) > 0

        validation_gate = self.etl_path / "validation_gate.py"
        result["validation_gate_found"] = validation_gate.exists()

        if not result["great_expectations"]:
            result["status"] = "WARNING"
            self.hallazgos.append({
                "dimensión": "Contratos",
                "hallazgo": "Great Expectations no configurado",
                "recomendación": "Implementar suites de validación automáticas",
                "priority": "ALTO",
            })

        logger.info(f"   Status: {result['status']}")
        return result

    def _audit_data_flow(self) -> Dict[str, Any]:
        """Dimensión 4: Flujo de Datos"""
        result = {"status": "OK", "pipeline_flow": "API Kawak → Transform → Consolidado.xlsx → Indicadores"}

        mapeo_files = list(self.etl_path.glob("*mapeo*.py")) + list(self.etl_path.glob("*mapa*.py"))
        result["mapping_modules"] = len(mapeo_files)

        if len(mapeo_files) == 0:
            result["status"] = "WARNING"
            self.hallazgos.append({
                "dimensión": "Flujo",
                "hallazgo": "No se encontraron módulos de mapeo",
                "recomendación": "Centralizar lógica de mapeo de campos",
                "priority": "MEDIO",
            })

        logger.info(f"   Status: {result['status']}")
        return result

    def _audit_versioning(self) -> Dict[str, Any]:
        """Dimensión 5: Versionado"""
        result = {"status": "OK", "has_version_manager": False, "has_audit_trail": False}

        actualizar = self.scripts_path / "actualizar_consolidado.py"
        if actualizar.exists():
            try:
                content = actualizar.read_text(encoding="utf-8", errors="ignore")
                result["has_version_manager"] = "VersionManager" in content
                result["has_audit_trail"] = "AuditTrail" in content

                if not result["has_version_manager"] or not result["has_audit_trail"]:
                    result["status"] = "WARNING"
                    self.hallazgos.append({
                        "dimensión": "Versionado",
                        "hallazgo": "VersionManager o AuditTrail no completamente integrados",
                        "priority": "MEDIO",
                    })
            except Exception:
                pass

        logger.info(f"   Status: {result['status']}")
        return result

    def _audit_error_handling(self) -> Dict[str, Any]:
        """Dimensión 6: Manejo de Errores"""
        result = {"status": "OK", "try_except_blocks": 0, "error_logging": False}

        actualizar = self.scripts_path / "actualizar_consolidado.py"
        if actualizar.exists():
            try:
                content = actualizar.read_text(encoding="utf-8", errors="ignore")
                result["try_except_blocks"] = content.count("try:")
                result["error_logging"] = "logger.error" in content
            except Exception:
                pass

        logger.info(f"   Status: {result['status']}")
        return result

    def _audit_modularity(self) -> Dict[str, Any]:
        """Dimensión 7: Modularidad"""
        etl_files = list(self.etl_path.glob("*.py"))
        result = {
            "status": "OK" if len(etl_files) > 5 else "WARNING",
            "module_count": len(etl_files),
            "modules": sorted([f.name for f in etl_files])[:10],
        }

        logger.info(f"   Status: {result['status']}")
        return result

    def _audit_configuration(self) -> Dict[str, Any]:
        """Dimensión 8: Configuración"""
        result = {"status": "OK", "config_files": []}

        config_patterns = ["config*.py", "*.toml", "*.yaml", ".env*"]
        for pattern in config_patterns:
            result["config_files"].extend([f.name for f in self.root.glob(pattern)])

        result["config_files"] = list(set(result["config_files"]))

        if not result["config_files"]:
            result["status"] = "WARNING"
            self.hallazgos.append({
                "dimensión": "Configuración",
                "hallazgo": "No se encontraron archivos de configuración",
                "recomendación": "Crear config.py centralizado",
                "priority": "MEDIO",
            })

        logger.info(f"   Status: {result['status']}")
        return result


def main():
    """Ejecutar auditoría ETL"""
    auditor = ETLPipelineAudit()
    results = auditor.audit_all()

    output_dir = Path(__file__).parent.parent / "artifacts"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = output_dir / f"AGENT2_ETL_AUDIT_{timestamp}.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"\n✅ Auditoría completada")
    logger.info(f"   Reporte guardado: {json_file}")
    logger.info(f"\n📊 Resumen:")
    logger.info(f"   Total hallazgos: {results['summary']['total_hallazgos']}")
    logger.info(f"   Críticos: {results['summary']['criticos']}")
    logger.info(f"   Altos: {results['summary']['altos']}")

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    main()
