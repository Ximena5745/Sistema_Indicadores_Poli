"""Contract validation gate over the real SGIND source files."""

from services.data_validation import validate_all_sources


def test_all_real_sources_match_contracts() -> None:
    reports = validate_all_sources()

    failures = []
    for source_name, report in reports.items():
        if not report.issues:
            continue

        # Separar errores de warnings
        errors = [i for i in report.issues if i.level == "error"]
        warnings = [i for i in report.issues if i.level == "warning"]

        # Ignorar fuentes cuyo archivo no existe (entorno sin datos reales)
        file_not_found = any(
            "not found" in (i.description or "").lower()
            for i in errors
        )
        if file_not_found:
            # Fuente no disponible en este entorno — skip silencioso
            continue

        # Solo fallar por ERRORs reales (no por warnings de calidad de datos)
        if errors:
            error_lines = [
                f"  error sheet={i.sheet} column={i.column}: {i.description}"
                for i in errors[:5]
            ]
            failures.append(
                f"{source_name}: {len(errors)} errores\n" + "\n".join(error_lines)
            )

    assert not failures, "\n\n".join(failures)
