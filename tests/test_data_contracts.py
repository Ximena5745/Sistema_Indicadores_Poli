"""Contract validation gate over the real SGIND source files."""

from services.data_validation import validate_all_sources


def test_all_real_sources_match_contracts() -> None:
    reports = validate_all_sources()

    failures = []
    for source_name, report in reports.items():
        if report.issues:
            issue_lines = [
                f"{issue.level} sheet={issue.sheet} column={issue.column} desc={issue.description}"
                for issue in report.issues[:5]
            ]
            failures.append(
                f"{source_name}: {len(report.issues)} issues\n" + "\n".join(issue_lines)
            )

    assert not failures, "\n\n".join(failures)