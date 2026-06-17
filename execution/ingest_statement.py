from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd

_CANONICAL_COLUMNS = ["date", "description", "amount", "side"]


def infer_side(amount: float) -> str:
    return "in" if amount >= 0 else "out"


def _normalise_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "Date": "date",
            "Description": "description",
            "Amount": "amount",
        }
    )
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["amount"] = df["amount"].round(2).astype(float)
    df["side"] = df["amount"].apply(infer_side)
    return df[_CANONICAL_COLUMNS]


def normalise_statement(path: Union[str, Path], password: Optional[str] = None) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path)

    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, engine="openpyxl" if suffix == ".xlsx" else None)

    elif suffix == ".pdf":
        import pdfplumber

        tables = []
        pdf_password = password if password else None
        with pdfplumber.open(str(path), password=pdf_password) as pdf:
            for page in pdf.pages:
                extracted = page.extract_table() or []
                tables.extend(extracted)

        rows = [row for row in tables if row and row != tables[0]]
        df = pd.DataFrame(rows[1:], columns=rows[0]) if rows else pd.DataFrame()
        if df.empty:
            return pd.DataFrame(columns=_CANONICAL_COLUMNS)

    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return _normalise_dataframe(df)
