# jjbank Implementation Plan

> **For Hermes:** Use subagent-driven-development to implement this plan task-by-task.

**Goal:** Build a standalone local bank statement analyser that ingests CSV, XLSX, and password-protected PDF statements, separates money in and out, tracks monthly depositors with missing-payment alerts, classifies spending, and surfaces results in a browser dashboard plus exportable local reports.

**Architecture:** Local-only Python app under `Documents/jjbank` with deterministic ingestion scripts in `execution/`, workflow rules in `directives/`, pytest tests in `tests/`, and a Streamlit dashboard for visual review.

**Tech Stack:** Python 3.11+, pandas, pytest, pypdf/pdfplumber, Streamlit

---

### Task 1: Initialise project and dependency baseline

**Objective:** Set up Python package scaffolding, virtual environment, and locked dependencies.

**Files:**
- Create: `Documents/jjbank/pyproject.toml`
- Create: `Documents/jjbank/requirements.txt`
- Create: `Documents/jjbank/.gitignore`
- Create: `Documents/jjbank/execution/__init__.py`
- Create: `Documents/jjbank/tests/__init__.py`

**Step 1: Write pyproject.toml**

Include build-system, project name `jjbank`, Python `>=3.11`, runtime deps (`pandas`, `openpyxl`, `pypdf`, `pdfplumber`, `streamlit`), and dev deps (`pytest`, `pytest-cov`).

**Step 2: Write .gitignore**

Ignore `.tmp/`, `.venv/`, `__pycache__/`, `.env`, `credentials*.json`, and build outputs.

**Step 3: Verify install**

Run:
```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```
Expected: install completes without errors.

**Step 4: Commit**

```bash
git add .
git commit -m "chore: initialise jjbank project"
```

---

### Task 2: Normalise raw bank exports into a canonical schema

**Objective:** Support CSV, XLSX, and password-protected PDFs, normalising every source to `date`, `description`, `amount`, `side` (`in`/`out`).

**Files:**
- Create: `execution/ingest_statement.py`
- Test: `tests/test_ingest_statement.py`

**Step 1: Write failing tests**

```python
import pathlib

def test_normalise_csv(tmp_path):
    path = tmp_path / "statement.csv"
    path.write_text("Date,Description,Amount\n2026-01-01,PAY IN,50.00\n2026-01-02,CARD DEBIT,-20.00\n")
    from execution.ingest_statement import normalise_statement
    rows = normalise_statement(str(path))
    assert len(rows) == 2
    assert rows[0]["amount"] == 50.0 and rows[0]["side"] == "in"
    assert rows[1]["amount"] == -20.0 and rows[1]["side"] == "out"

def test_normalise_xlsx(tmp_path):
    path = tmp_path / "statement.xlsx"
    import pandas as pd
    pd.DataFrame([{"Date":"2026-01-01","Description":"DEP","Amount":100.0}]).to_excel(path, index=False)
    from execution.ingest_statement import normalise_statement
    rows = normalise_statement(str(path))
    assert rows[0]["amount"] == 100.0 and rows[0]["side"] == "in"

def test_normalise_password_protected_pdf(tmp_path):
    path = pathlib.Path(__file__).with_name("fixtures") / "sample_password_protected.pdf"
    if not path.exists():
        return  # skip when fixture missing
    from execution.ingest_statement import normalise_statement
    rows = normalise_statement(str(path), password="secret")
    assert any(r["side"] == "out" for r in rows)
```

**Step 2: Run tests to verify failure**

Run:
```bash
pytest tests/test_ingest_statement.py -v
```
Expected: FAIL — no module and missing password PDF fixture handling.

**Step 3: Write minimal implementation**

In `execution/ingest_statement.py`:
- Add `infer_side(amount)` returning `"in"` if `>= 0` else `"out"`.
- Add PDF reader using `pypdf.PdfReader(..., password=password)` and extract tables/text into transactions.
- Add CSV reader via `csv.DictReader`.
- Add XLSX reader via `pandas.read_excel`.
- Normalise all sources to the canonical schema and round amounts to 2 decimal places.

**Step 4: Run tests to verify pass**

Run:
```bash
pytest tests/test_ingest_statement.py -v
```
Expected: PASS for existing fixtures; skip gracefully if PDF fixture absent.

**Step 5: Commit**

```bash
git add execution/ingest_statement.py tests/test_ingest_statement.py
git commit -m "feat: normalise CSV, XLSX, and password-protected PDF statements"
```

---

### Task 3: Classify expenses into spend categories

**Objective:** Convert outflows into consistent categories via simple keyword rules and “uncategorised” fallback.

**Files:**
- Create: `execution/categorise.py`
- Test: `tests/test_categorise.py`

**Step 1: Write failing test**

```python
def test_keyword_rules_categorise_description():
    from execution.categorise import categorise_transaction
    assert categorise_transaction("Tesco groceries") == "groceries"
    assert categorise_transaction("Uber trip to airport") == "transport"
    assert categorise_transaction("Council tax monthly") == "bills"
    assert categorise_transaction("Random transfer ABC 123") == "uncategorised"
```

**Step 2: Run test to verify failure**

Run:
```bash
pytest tests/test_categorise.py::test_keyword_rules_categorise_description -v
```
Expected: FAIL

**Step 3: Write minimal implementation**

In `execution/categorise.py`:
- Define `_RULES` with categories and lowercase keywords.
- Implement `categorise_transaction(description)` returning first match or `"uncategorised"`.

**Step 4: Run test to verify pass**

Run:
```bash
pytest tests/test_categorise.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add execution/categorise.py tests/test_categorise.py
git commit -m "feat: add keyword-based expense categorisation"
```

---

### Task 4: Detect recurring depositors and missing-payment alerts

**Objective:** Identify payers who deposit in multiple months and generate missing-payment alerts for expected-but-absent months.

**Files:**
- Create: `execution/income_analysis.py`
- Test: `tests/test_income_analysis.py`

**Step 1: Write failing test**

```python
def test_monthly_depositor_detection_and_missing_flag():
    rows = [
        {"date": "2026-01-01", "description": "Income from Alan", "amount": 1200, "side": "in"},
        {"date": "2026-02-01", "description": "Income from Alan", "amount": 1200, "side": "in"},
        {"date": "2026-03-01", "description": "Income from Alan", "amount": 1200, "side": "in"},
        {"date": "2026-01-01", "description": "Transfer from Beth", "amount": 300, "side": "in"},
        {"date": "2026-02-01", "description": "Transfer from Beth", "amount": 300, "side": "in"},
    ]
    from execution.income_analysis import analyse_income
    result = analyse_income(rows)
    assert any(item["name"] == "Alan" for item in result["monthly_depositors"])
    assert any(item["name"] == "Beth" and item["month"] == "2026-03" for item in result["alerts"])
```

**Step 2: Run test to verify failure**

Run:
```bash
pytest tests/test_income_analysis.py::test_monthly_depositor_detection_and_missing_flag -v
```
Expected: FAIL

**Step 3: Write minimal implementation**

In `execution/income_analysis.py`:
- Normalise payer names from common prefixes: `Income from`, `Transfer from`, `Deposit from`.
- Group deposits by payer and month.
- Mark payers with activity in `>=2` months as `monthly_depositors`.
- Build alerts for gaps compared to the observed month range.

**Step 4: Run test to verify pass**

Run:
```bash
pytest tests/test_income_analysis.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add execution/income_analysis.py tests/test_income_analysis.py
git commit -m "feat: detect recurring depositors and missing payment alerts"
```

---

### Task 5: Build local report exports

**Objective:** Produce deterministic JSON and Markdown report outputs from analysed data.

**Files:**
- Create: `execution/reports.py`
- Test: `tests/test_reports.py`

**Step 1: Write failing test**

```python
def test_spending_summary_groups_by_category():
    rows = [
        {"date": "2026-03-01", "description": "Tesco groceries", "amount": -90.0, "side": "out", "category": "groceries"},
        {"date": "2026-03-02", "description": "Uber trip", "amount": -20.0, "side": "out", "category": "transport"},
        {"date": "2026-03-03", "description": "Shell fuel", "amount": -35.0, "side": "out", "category": "transport"},
    ]
    from execution.reports import spending_summary
    summary = spending_summary(rows)
    assert summary["categories"]["transport"] == 55.0
    assert summary["categories"]["groceries"] == 90.0
    assert summary["total_out"] == 145.0
```

**Step 2: Run test to verify failure**

Run:
```bash
pytest tests/test_reports.py::test_spending_summary_groups_by_category -v
```
Expected: FAIL

**Step 3: Write minimal implementation**

In `execution/reports.py`:
- Implement `spending_summary(rows)` summing absolute outflows by category.
- Implement `income_summary(rows, monthly_depositors, alerts)` summarising deposits.
- Implement `render_markdown(summary, income_summary)` producing a simple readable report.

**Step 4: Run test to verify pass**

Run:
```bash
pytest tests/test_reports.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add execution/reports.py tests/test_reports.py
git commit -m "feat: add local spending and income reports"
```

---

### Task 6: Build the browser dashboard

**Objective:** Provide a local web UI for review, upload, analysis, and report download.

**Files:**
- Create: `cli.py`
- Create: `web/app.py`
- Create: `web/pages/upload.py` (optional split later)
- Create: `Documents/jjbank/.tmp` placeholder (gitignored)

**Step 1: Add CLI entrypoint**

`cli.py` should:
- Accept `--statement <path>` and `--out <path>`.
- Run the full pipeline: ingest → categorise → income analysis → reports.
- Write JSON and Markdown reports to `.tmp/`.

**Step 2: Verify CLI**

Run:
```bash
python cli.py --statement tests/fixtures/sample.csv --out .tmp/report.json
```
Expected: `.tmp/report.json` is created.

**Step 3: Add Streamlit dashboard**

In `web/app.py`:
- Provide file uploader for CSV, XLSX, PDF.
- If PDF: ask for password via text input.
- Run the pipeline on upload.
- Show: Money In/Out totals.
- Show: Recurring depositors table.
- Show: Alerts table (missing payments).
- Show: Spending breakdown chart by category.
- Provide download button for `.tmp/report.json` and `.tmp/report.md`.

Run dashboard:
```bash
streamlit run web/app.py
```
Expected: Browser opens at `http://localhost:8501` and uploads work.

**Step 4: Commit**

```bash
git add cli.py web/app.py .tmp .gitignore
git commit -m "feat: add Streamlit dashboard and CLI"
```

---

## Tests / Validation

Run the full suite after each Task 2–5:
```bash
pytest -q
```

Manual validation:
```bash
python cli.py --statement <sample file> --out .tmp/report.json
streamlit run web/app.py
```

Expected green pytest and a working dashboard in the browser.

## Files likely to change

- `execution/ingest_statement.py`
- `execution/categorise.py`
- `execution/income_analysis.py`
- `execution/reports.py`
- `cli.py`
- `web/app.py`
- `tests/test_ingest_statement.py`
- `tests/test_categorise.py`
- `tests/test_income_analysis.py`
- `tests/test_reports.py`
- `directives/statement_analysis.md`

## Risks and Tradeoffs

- PDF password extraction relies on correct password entry; no recovery if wrong.
- Keyword categorisation is heuristic in V1 and may miss custom merchant names.
- Very large statements may need batching later (not required for V1).
- Streamlit is convenient but not embedded-electron; if a more polished standalone exe is needed later, packaging is the next step after V1 approval.
