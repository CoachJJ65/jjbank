from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest
import xlsxwriter

import execution.ingest_statement as ingest


def _write_csv(path: Path, df: pd.DataFrame) -> None:
    df.to_csv(path, index=False)


def _write_xlsx(path: Path, df: pd.DataFrame) -> None:
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)


def _make_password_protected_pdf(path: Path, password: str) -> None:
    try:
        import fpdf  # noqa: F401
    except ModuleNotFoundError:
        pytest.skip("fpdf not installed; skipping password-protected PDF fixture test")

    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, txt="Date,Description,Amount", ln=True)
    pdf.cell(200, 10, txt="2024-01-01,Test,10.50", ln=True)
    pdf.set_encryption(password)
    pdf.output(str(path))


class TestIngestStatement:
    def test_infer_side(self):
        assert ingest.infer_side(0.0) == "in"
        assert ingest.infer_side(10.0) == "in"
        assert ingest.infer_side(-5.0) == "out"
        assert ingest.infer_side(2 ** 63) == "in"

    def test_normalise_csv(self, tmp_path: Path):
        csv_path = tmp_path / "statement.csv"
        _write_csv(
            csv_path,
            pd.DataFrame(
                {
                    "Date": ["2024-01-01", "2024-01-02"],
                    "Description": ["Coffee", "Salary"],
                    "Amount": [10.50, -100.00],
                }
            ),
        )
        result = ingest.normalise_statement(str(csv_path))
        assert list(result.columns) == ["date", "description", "amount", "side"]
        assert len(result) == 2
        assert result.loc[0, "date"] == "2024-01-01"
        assert result.loc[0, "amount"] == 10.50
        assert result.loc[0, "side"] == "in"
        assert result.loc[1, "side"] == "out"
        assert abs(result["amount"].sum() - (-89.50)) < 1e-6

    def test_normalise_xlsx(self, tmp_path: Path):
        xlsx_path = tmp_path / "statement.xlsx"
        _write_xlsx(
            xlsx_path,
            pd.DataFrame(
                {
                    "Date": ["2024-01-01", "2024-01-02"],
                    "Description": ["Coffee", "Salary"],
                    "Amount": [10.50, -100.00],
                }
            ),
        )
        result = ingest.normalise_statement(str(xlsx_path))
        assert list(result.columns) == ["date", "description", "amount", "side"]
        assert len(result) == 2
        assert result.loc[0, "date"] == "2024-01-01"
        assert result.loc[0, "amount"] == 10.50
        assert result.loc[1, "amount"] == -100.00

    def test_normalise_password_protected_pdf(self, tmp_path: Path):
        pdf_path = tmp_path / "statement.pdf"
        _make_password_protected_pdf(pdf_path, "secret123")
        result = ingest.normalise_statement(str(pdf_path), password="secret123")
        assert list(result.columns) == ["date", "description", "amount", "side"]
        assert len(result) == 1
        assert result.loc[0, "amount"] == 10.50
