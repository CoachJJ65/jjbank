from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd
import re

_CANONICAL_COLUMNS = ["date", "description", "amount", "side"]


def infer_side(amount):
    return "in" if amount >= 0 else "out"


_COLUMN_RENAME_MAP = {
    "Date": "date",
    "Description": "description",
    "Amount": "amount",
    "Balance": "balance",
    "Type": "type",
    "Details": "description",
    "Memo": "description",
    "Reference": "reference",
}


def _normalise_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "date" in df.columns:
        df = df.rename(columns=_COLUMN_RENAME_MAP)
    if "date" not in df.columns:
        for candidate in df.columns:
            text = str(candidate).lower()
            if "date" in text:
                df = df.rename(columns={candidate: "date"})
                break

    if "amount" in df.columns:
        df = df.rename(columns=_COLUMN_RENAME_MAP)
    if "amount" not in df.columns:
        for candidate in df.columns:
            text = str(candidate).lower()
            if any(token in text for token in ["amount", "debit", "credit", "balance"]):
                df = df.rename(columns={candidate: "amount"})
                break

    if "description" not in df.columns:
        for candidate in df.columns:
            text = str(candidate).lower()
            if any(token in text for token in ["desc", "details", "narr", "memo"]):
                df = df.rename(columns={candidate: "description"})
                break

    if "date" not in df.columns:
        raise ValueError("Missing date column in parsed data")

    if "amount" not in df.columns:
        df["amount"] = 0.0
    if "description" not in df.columns:
        df["description"] = ""

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").round(2)
    df = df.dropna(subset=["date", "amount"])
    df["description"] = df["description"].fillna("").astype(str)
    df["side"] = df["amount"].apply(infer_side)
    return reorder_columns_safely(df)


def reorder_columns_safely(df):
    for column in _CANONICAL_COLUMNS:
        if column not in df.columns:
            df[column] = ""
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
        import traceback

        text_pages = []
        pdf_password = password if password else None
        try:
            with pdfplumber.open(str(path), password=pdf_password) as pdf:
                for page in pdf.pages:
                    extracted_text = page.extract_text()
                    if extracted_text:
                        text_pages.append(extracted_text)
        except Exception as exc:
            print(traceback.format_exc())
            raise RuntimeError(f"Failed to open PDF: {exc}") from exc

        full_text = "\n".join(text_pages)
        if not full_text.strip():
            return pd.DataFrame(columns=_CANONICAL_COLUMNS)

        rows = _parse_bank_text_lines(full_text)
        if not rows:
            return pd.DataFrame(columns=_CANONICAL_COLUMNS)
        df = pd.DataFrame(rows)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return _normalise_dataframe(df)


_DATE_PATTERNS = [
    r"(?P<date>\d{4}[-/]\d{1,2}[-/]\d{1,2})",
    r"(?P<date>\d{1,2}[-/]\d{1,2}[-/]\d{4})",
    r"(?P<date>\d{1,2}[-/][A-Za-z]{3}[-/]\d{4})",
]

_AMOUNT_PATTERNS = [
    r"(?P<amount>-?\d{1,3}(?:,\d{3})*\.\d{2})",
    r"(?P<amount>-?\d+\.\d{2})",
    r"(?P<amount>[\(\-]\d{1,3}(?:,\d{3})*\.\d{2}\)?)",
]


def _build_combined_pattern():
    date_group = "|".join(_DATE_PATTERNS)
    amt_group = "|".join(_AMOUNT_PATTERNS)
    return re.compile(
        rf"""
        (?P<line>
            .*?
            (?:{date_group})
            .*?
            (?:{amt_group})
            .*?
        )
        """,
        re.VERBOSE | re.IGNORECASE,
    )


def _parse_amount_token(raw: str) -> float:
    text = raw.strip().replace(",", "")
    if text.startswith("(") and ")" in text:
        text = "-" + text.strip("()")
    return float(text)


def _parse_bank_text_lines(text: str):
    pattern = _build_combined_pattern()
    rows = []
    seen = set()
    lines = text.splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        match = pattern.search(line)
        if not match:
            continue
        date = match.group("date")
        amount = _parse_amount_token(match.group("amount"))
        description = line[: match.start()] + line[match.end() :]
        description = re.sub(r"\s+", " ", description).strip(" -:|")
        key = (date, description, amount)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "date": date,
                "description": description or "Transaction",
                "amount": amount,
            }
        )
    return rows
