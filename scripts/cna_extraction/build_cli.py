"""
scripts/cna_extraction/build_cli.py

Entrypoint de la Fase 2: recorre el catálogo + detector de estructura,
normaliza al esquema de Metricas y escribe incrementalmente en
data/output/Resultados_Consolidados_CNA.xlsx (nunca en data/raw/).

Deliberadamente separado de cli.py (Fase 1, solo diagnóstico) para que el
límite de "Fase 1 no escribe nada" siga siendo válido sin tocar ese módulo.

Uso:
    python -m scripts.cna_extraction.build_cli --write
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import openpyxl

from core.config import DATA_RAW
from scripts.cna_extraction.catalog import build_factor_caracteristica_rows, load_catalog
from scripts.cna_extraction.normalize import build_metricas_rows
from scripts.cna_extraction.sheet_resolver import resolve_sheets
from scripts.cna_extraction.structure_detector import detect_structure
from scripts.cna_extraction.writer import OUTPUT_FILE, write_incremental
from scripts.etl.audit import AuditTrail

DEFAULT_SOURCE = DATA_RAW / "Plan de mejoramiento" / "Anexo Estadístico Dcto. Autoevaluacion.xlsx"


def build_records(xlsx_path: Path) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, str]]]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    try:
        catalog = load_catalog(xlsx_path)
        resolved, _ = resolve_sheets(catalog, wb)
        stats = {"valores_cualitativos_no_convertidos": 0, "totales_calculados_por_suma": 0}
        all_records: list[dict[str, Any]] = []

        for item in resolved:
            if item.sheet_name is None or item.catalog_record is None:
                continue
            ws = wb[item.sheet_name]
            raw_rows = [list(row) for row in ws.iter_rows(values_only=True)]
            structure = detect_structure(raw_rows, item.catalog_record.numero)
            all_records.extend(build_metricas_rows(structure, item.catalog_record, stats))

        factor_caracteristica_rows = build_factor_caracteristica_rows(catalog)
        return all_records, stats, factor_caracteristica_rows
    finally:
        wb.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fase 2 — construye/actualiza el consolidado CNA en data/output/ (incremental)."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        required=True,
        help="Confirma la escritura incremental (única acción disponible).",
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Ruta al Anexo Estadístico.")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE, help="Archivo de salida (data/output/).")
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"No se encontró el archivo fuente: {args.source}")

    records, stats, factor_caracteristica_rows = build_records(args.source)
    result = write_incremental(records, args.output, factor_caracteristica_rows=factor_caracteristica_rows)

    try:
        AuditTrail().registrar_ejecucion(
            evento="build_consolidado_cna",
            detalles={**result, **stats, "archivo_salida": str(args.output)},
            exitoso=True,
        )
    except Exception:
        pass

    print(f"Archivo de salida: {args.output}")
    print(f"Registros existentes antes de esta corrida: {result['registros_existentes']}")
    print(f"Registros nuevos insertados: {result['registros_nuevos_insertados']}")
    print(f"Registros totales tras la corrida: {result['registros_totales']}")
    print(f"Valores cualitativos no convertidos: {stats['valores_cualitativos_no_convertidos']}")
    print(f"Totales calculados por suma de subdivisiones: {stats['totales_calculados_por_suma']}")


if __name__ == "__main__":
    main()
