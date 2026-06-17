# jjbank

Standalone bank statement analyser that works with CSV, XLSX, and password-protected PDFs.

- Separates money in and money out
- Detects monthly depositors and missing payments
- Classifies spending
- Shows a browser dashboard
- Exports JSON and Markdown reports

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

Double-click `run.bat` or use:

```powershell
.\.venv\Scripts\activate
streamlit run web/app.py
```

## CLI

```powershell
python cli.py --statement <statement_path> --out .tmp\report.json
```

## Project layout

- `execution/` - ingest, categorise, income analysis, reports
- `tests/` - pytest suite
- `web/app.py` - Streamlit dashboard
- `cli.py` - local command-line export

## Privacy

Runs locally. No cloud sync or external accounts required.
