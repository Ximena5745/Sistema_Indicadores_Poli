"""
scripts/agent3_indicator_integrity.py
AGENT 3 — Indicator Integrity Analysis
Audita integridad, unicidad y consistencia de indicadores SGIND
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class IndicatorIntegrityAudit:
    """Auditoría de integridad de indicadores SGIND"""

    def __init__(self, root_path: Path | None = None):
        self.root = Path(root_path) if root_path else Path(__file__).parent.parent
        self.indicators: Dict[str, Dict[str, Any]] = {}
        self.hallazgos: List[Dict[str, Any]] = []
        self.duplicates: List[List[str]] = []

    def run_audit(self) -> Dict[str, Any]:
        """Ejecutar auditoría completa"""
        logger.info("=" * 70)
        logger.info("AGENT 3 — Indicator Integrity Analysis")
        logger.info("=" * 70)

        self._discover_indicators()
        self._audit_formulas()
        self._audit_metadata()
        self._detect_duplicates()
        self._audit_documentation()

        return {
            "timestamp": datetime.now().isoformat(),
            "framework": "SGIND v1.0",
            "total_indicadores": len(self.indicators),
            "hallazgos": self.hallazgos,
            "duplicates": self.duplicates,
            "indicadores": self.indicators,
            "metrics": self._calculate_metrics(),
        }

    def _discover_indicators(self):
        """Descubrir indicadores en codebase"""
        logger.info("\n📋 Descubriendo indicadores...")

        # Indicadores descubiertos (simulado - en producción escanear archivos)
        default_indicators = {
            "cumplimiento_academico": {
                "nombre": "Cumplimiento Académico",
                "tipo": "base",
                "perspectiva": "Procesos",
                "proceso": "Académica",
                "periodicidad": "Mensual",
                "fuente": "Kawak",
                "linea_base": None,
                "meta": None,
                "responsable": None,
            },
            "cumplimiento_administrativo": {
                "nombre": "Cumplimiento Administrativo",
                "tipo": "base",
                "perspectiva": "Procesos",
                "proceso": "Administrativa",
                "periodicidad": "Mensual",
                "fuente": "Kawak",
                "linea_base": None,
                "meta": None,
                "responsable": None,
            },
            "ejecucion_presupuestal": {
                "nombre": "Ejecución Presupuestal",
                "tipo": "base",
                "perspectiva": "Financiera",
                "proceso": "Financiera",
                "periodicidad": "Mensual",
                "fuente": "Excel",
                "linea_base": 0.0,
                "meta": 0.95,
                "responsable": "Dirección Financiera",
            },
            "cmi_estrategico": {
                "nombre": "CMI Estratégico",
                "tipo": "compuesto",
                "perspectiva": "Todas",
                "proceso": "Corporativo",
                "periodicidad": "Mensual",
                "fuente": "Consolidado",
                "linea_base": 0.5,
                "meta": 0.8,
                "responsable": "Dirección General",
            },
        }

        self.indicators = default_indicators
        logger.info(f"   Indicadores descubiertos: {len(self.indicators)}")

    def _audit_formulas(self):
        """Auditar unicidad y consistencia de fórmulas"""
        logger.info("\n📋 Auditando fórmulas...")

        # Fórmulas simuladas (en producción buscar en código real)
        formulas_in_docs = {
            "cumplimiento_academico": "(Cumplidos / Total) * 100",
            "cumplimiento_administrativo": "(Ejecutado / Planeado) * 100",
            "ejecucion_presupuestal": "(Gastos / Presupuesto) * 100",
            "cmi_estrategico": "(Academico*0.3 + Administrativo*0.4 + Financiero*0.3)",
        }

        formulas_in_code = {
            "cumplimiento_academico": "(df['Cumplidos'] / df['Total']) * 100",
            "cumplimiento_administrativo": "(df['Ejecutado'] / df['Planeado']) * 100",
            "ejecucion_presupuestal": "(df['Gastos'] / df['Presupuesto']) * 100",
            "cmi_estrategico": "(ac*0.3 + ad*0.4 + fn*0.3)",  # Diferente sintaxis
        }

        for ind_id, ind_data in self.indicators.items():
            docs_formula = formulas_in_docs.get(ind_id, "NO DOCUMENTADA")
            code_formula = formulas_in_code.get(ind_id, "NO IMPLEMENTADA")

            # Simplicidad: coincidencia de variables clave
            coincide = self._formulas_match(docs_formula, code_formula)

            if not coincide and ind_id in formulas_in_docs:
                self.hallazgos.append({
                    "id": f"FORMULA_{ind_id}",
                    "tipo": "Fórmula Inconsistente",
                    "severidad": "CRÍTICA",
                    "indicador": ind_data["nombre"],
                    "formula_docs": docs_formula,
                    "formula_code": code_formula,
                    "impacto": "Posible inconsistencia en cálculos",
                    "recomendacion": "Validar y sincronizar fórmulas en docs y código",
                })

            ind_data["formula_docs"] = docs_formula
            ind_data["formula_code"] = code_formula
            ind_data["formula_coincide"] = coincide

        logger.info(f"   Fórmulas auditadas: {len(self.indicators)}")

    def _audit_metadata(self):
        """Auditar completitud de metadatos"""
        logger.info("\n📋 Auditando metadatos...")

        for ind_id, ind_data in self.indicators.items():
            issues = []

            # Línea base
            if ind_data.get("linea_base") is None:
                issues.append("linea_base_faltante")

            # Meta
            if ind_data.get("meta") is None:
                issues.append("meta_faltante")

            # Responsable
            if ind_data.get("responsable") is None:
                issues.append("responsable_no_asignado")

            # Registrar hallazgos
            for issue in issues:
                issue_map = {
                    "linea_base_faltante": (
                        "Línea Base Faltante",
                        "MEDIA",
                        "Indicador sin línea base documentada"
                    ),
                    "meta_faltante": (
                        "Meta Faltante",
                        "MEDIA",
                        "Indicador sin meta definida"
                    ),
                    "responsable_no_asignado": (
                        "Responsable No Asignado",
                        "BAJA",
                        "Nadie es accountable por este indicador"
                    ),
                }

                tipo, severidad, impacto = issue_map.get(issue, ("Desconocido", "BAJA", ""))

                self.hallazgos.append({
                    "id": f"META_{ind_id}_{issue}",
                    "tipo": tipo,
                    "severidad": severidad,
                    "indicador": ind_data["nombre"],
                    "impacto": impacto,
                    "recomendacion": f"Definir {issue.replace('_', ' ').lower()}",
                })

            ind_data["metadata_issues"] = issues

    def _detect_duplicates(self):
        """Detectar indicadores duplicados"""
        logger.info("\n📋 Detectando duplicaciones...")

        seen_names = {}
        for ind_id, ind_data in self.indicators.items():
            nombre = ind_data["nombre"].lower()
            if nombre in seen_names:
                self.duplicates.append([seen_names[nombre], ind_id])
                self.hallazgos.append({
                    "id": f"DUP_{ind_id}",
                    "tipo": "Indicador Duplicado",
                    "severidad": "CRÍTICA",
                    "indicador": ind_data["nombre"],
                    "duplicado_con": self.indicators[seen_names[nombre]]["nombre"],
                    "impacto": "Inconsistencia garantizada entre reportes",
                    "recomendacion": "Consolidar en un único indicador",
                })
            else:
                seen_names[nombre] = ind_id

        logger.info(f"   Duplicaciones detectadas: {len(self.duplicates)}")

    def _audit_documentation(self):
        """Auditar completitud de documentación"""
        logger.info("\n📋 Auditando documentación...")

        for ind_id, ind_data in self.indicators.items():
            # Verificar que esté en docs
            doc_fields = ["formula_docs", "linea_base", "meta", "responsable"]
            missing_docs = [f for f in doc_fields if not ind_data.get(f)]

            if missing_docs:
                self.hallazgos.append({
                    "id": f"DOC_{ind_id}",
                    "tipo": "Documentación Incompleta",
                    "severidad": "MEDIA",
                    "indicador": ind_data["nombre"],
                    "campos_faltantes": missing_docs,
                    "impacto": "Imposible auditar indicador completamente",
                    "recomendacion": f"Documentar campos: {', '.join(missing_docs)}",
                })

    def _formulas_match(self, formula_docs: str, formula_code: str) -> bool:
        """Verificar si dos fórmulas coinciden (simplificado)"""
        if "NO DOCUMENTADA" in formula_docs or "NO IMPLEMENTADA" in formula_code:
            return False

        # Extraer variables clave (simplificado)
        vars_docs = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula_docs))
        vars_code = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula_code))

        # Coinciden si tienen las mismas variables clave
        return vars_docs == vars_code

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calcular métricas de auditoría"""
        total = len(self.indicators)
        con_linea_base = sum(1 for i in self.indicators.values() if i.get("linea_base") is not None)
        con_meta = sum(1 for i in self.indicators.values() if i.get("meta") is not None)
        con_responsable = sum(1 for i in self.indicators.values() if i.get("responsable"))
        formulas_inconsistentes = sum(1 for i in self.indicators.values() if not i.get("formula_coincide", True))

        return {
            "total_indicadores": total,
            "con_linea_base": con_linea_base,
            "con_meta": con_meta,
            "con_responsable": con_responsable,
            "formulas_inconsistentes": formulas_inconsistentes,
            "cobertura_linea_base": f"{(con_linea_base/total*100):.1f}%" if total > 0 else "0%",
            "cobertura_meta": f"{(con_meta/total*100):.1f}%" if total > 0 else "0%",
            "cobertura_responsable": f"{(con_responsable/total*100):.1f}%" if total > 0 else "0%",
            "total_hallazgos": len(self.hallazgos),
            "hallazgos_criticos": len([h for h in self.hallazgos if h["severidad"] == "CRÍTICA"]),
            "hallazgos_altos": len([h for h in self.hallazgos if h["severidad"] == "ALTA"]),
            "hallazgos_medios": len([h for h in self.hallazgos if h["severidad"] == "MEDIA"]),
        }

    def export_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generar reporte Markdown"""
        metrics = results["metrics"]

        report = [
            "# AGENT 3 — Indicator Integrity Audit Report",
            "",
            f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Framework:** SGIND v1.0  ",
            "",
            "## Resumen Ejecutivo",
            "",
            f"- **Total indicadores auditados:** {metrics['total_indicadores']}",
            f"- **Con línea base:** {metrics['con_linea_base']} ({metrics['cobertura_linea_base']})",
            f"- **Con meta:** {metrics['con_meta']} ({metrics['cobertura_meta']})",
            f"- **Con responsable:** {metrics['con_responsable']} ({metrics['cobertura_responsable']})",
            f"- **Fórmulas inconsistentes:** {metrics['formulas_inconsistentes']} ⚠️",
            "",
            "## Hallazgos por Severidad",
            "",
            f"### 🔴 CRÍTICOS ({metrics['hallazgos_criticos']})",
            "",
        ]

        # Hallazgos críticos
        for hallazgo in [h for h in self.hallazgos if h["severidad"] == "CRÍTICA"]:
            report.append(f"- **{hallazgo['indicador']}** — {hallazgo['tipo']}")
            report.append(f"  {hallazgo['impacto']}")
            report.append(f"  ↳ {hallazgo['recomendacion']}")
            report.append("")

        report.extend([
            f"### 🟠 ALTOS ({metrics['hallazgos_altos']})",
            "",
        ])

        # Hallazgos altos
        for hallazgo in [h for h in self.hallazgos if h["severidad"] == "ALTA"][:3]:
            report.append(f"- **{hallazgo.get('indicador', 'N/A')}** — {hallazgo['tipo']}")

        report.extend([
            "",
            f"### 🟡 MEDIOS ({metrics['hallazgos_medios']})",
            f"[{metrics['hallazgos_medios']} hallazgos adicionales en reportes detallados]",
            "",
            "## Indicadores Auditados",
            "",
        ])

        # Tabla de indicadores
        report.append("| Indicador | Tipo | LB | Meta | Resp. | Fórmula OK |")
        report.append("|-----------|------|----|----|--------|----------|")

        for ind_id, ind_data in sorted(self.indicators.items()):
            lb = "✅" if ind_data.get("linea_base") is not None else "❌"
            meta = "✅" if ind_data.get("meta") is not None else "❌"
            resp = "✅" if ind_data.get("responsable") else "❌"
            formula = "✅" if ind_data.get("formula_coincide") else "❌"

            report.append(
                f"| {ind_data['nombre']} | {ind_data['tipo']} | {lb} | {meta} | {resp} | {formula} |"
            )

        return "\n".join(report)

    def export_csv_matriz(self) -> str:
        """Exportar matriz de auditoría en CSV"""
        lines = ["Indicador,Tipo,Línea Base,Meta,Responsable,Fórmula OK,Hallazgos"]

        for ind_id, ind_data in self.indicators.items():
            issues_count = len([h for h in self.hallazgos if h.get("indicador") == ind_data["nombre"]])
            lb = "Sí" if ind_data.get("linea_base") is not None else "No"
            meta = "Sí" if ind_data.get("meta") is not None else "No"
            resp = "Sí" if ind_data.get("responsable") else "No"
            formula = "Sí" if ind_data.get("formula_coincide") else "No"

            line = (
                f'{ind_data["nombre"]},{ind_data["tipo"]},{lb},{meta},{resp},{formula},{issues_count}'
            )
            lines.append(line)

        return "\n".join(lines)

    def export_hallazgos_json(self) -> str:
        """Exportar hallazgos en JSON"""
        hallazgos_grouped = {
            "CRÍTICA": [h for h in self.hallazgos if h["severidad"] == "CRÍTICA"],
            "ALTA": [h for h in self.hallazgos if h["severidad"] == "ALTA"],
            "MEDIA": [h for h in self.hallazgos if h["severidad"] == "MEDIA"],
            "BAJA": [h for h in self.hallazgos if h["severidad"] == "BAJA"],
        }

        return json.dumps(
            {
                "hallazgos_por_severidad": hallazgos_grouped,
                "total_por_severidad": {
                    k: len(v) for k, v in hallazgos_grouped.items()
                },
            },
            indent=2,
            ensure_ascii=False,
        )


def main():
    """Ejecutar auditoría de integridad"""
    audit = IndicatorIntegrityAudit()
    results = audit.run_audit()

    # Generar artefactos
    output_dir = Path(__file__).parent.parent / "artifacts"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Markdown
    md_file = output_dir / f"AGENT3_INDICATOR_INTEGRITY_{timestamp}.md"
    md_file.write_text(audit.export_markdown_report(results), encoding="utf-8")
    logger.info(f"   ✅ Markdown: {md_file}")

    # CSV
    csv_file = output_dir / f"AGENT3_INDICATOR_INTEGRITY_{timestamp}.csv"
    csv_file.write_text(audit.export_csv_matriz(), encoding="utf-8")
    logger.info(f"   ✅ CSV: {csv_file}")

    # Hallazgos JSON
    json_file = output_dir / f"AGENT3_INDICATOR_INTEGRITY_{timestamp}.json"
    json_file.write_text(audit.export_hallazgos_json(), encoding="utf-8")
    logger.info(f"   ✅ Hallazgos JSON: {json_file}")

    logger.info(f"\n✅ Auditoría completada")
    logger.info(f"\n📊 Métricas:")
    for key, value in results["metrics"].items():
        logger.info(f"   {key}: {value}")

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    main()
