"""CLI entrypoint for jjbank."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from execution.ingest_statement import normalise_statement
from execution.categorise import categorise_transaction
from execution.income_analysis import analyse_income
from execution.reports import build_report, render_markdown


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="jjbank",
        description="Analyse a bank statement and export a report.",
    )
    parser.add_argument(
        "--statement",
        required=True,
        help="Path to the statement file (CSV, XLSX, or PDF).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output path prefix for the exported report files.",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Optional password for encrypted PDF statements.",
    )
    args = parser.parse_args()

    statement = normalise_statement(args.statement, password=args.password)
    # analyse_income expects a "title" field; derive it from description.
    enriched = []
    for row in statement.to_dict(orient="records"):
        if "description" in row and "title" not in row:
            row["title"] = row["description"]
        enriched.append(row)

    report = build_report(enriched)
    report["source"] = str(args.statement)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    json_path = out_path.with_suffix(out_path.suffix + ".json") if out_path.suffix else out_path.with_suffix(".json")
    md_path = out_path.with_suffix(out_path.suffix + ".md") if out_path.suffix else out_path.with_suffix(".md")

    json_path.write_text(json.dumps(report, indent=2))
    md_path.write_text(render_markdown(report))

    print(f"Exported JSON report to {json_path}")
    print(f"Exported Markdown report to {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
