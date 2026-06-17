"""Standalone desktop GUI for jjbank."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from tkinter import Tk, filedialog, messagebox, simpledialog, ttk

import pandas as pd

from execution.ingest_statement import normalise_statement
from execution.reports import build_report, render_markdown


class JjBankApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("jjbank")
        self.root.geometry("980x680")

        self.report: dict = {}
        self.rows: list[dict] = []
        self.tmp_path: str | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Button(top, text="Open Statement", command=self._open_file).pack(side="left")
        self.file_label = ttk.Label(top, text="No file selected")
        self.file_label.pack(side="left", padx=10)

        self.password_var = ttk.StringVar()
        ttk.Label(top, text="PDF password:").pack(side="left")
        ttk.Entry(top, textvariable=self.password_var, show="*").pack(side="left", padx=6)

        ttk.Button(top, text="Analyse", command=self._analyse).pack(side="left", padx=10)

        self.money_in_var = ttk.StringVar(value="Money In: 0.00")
        self.money_out_var = ttk.StringVar(value="Money Out: 0.00")
        metrics = ttk.Frame(self.root, padding=10)
        metrics.pack(fill="x")
        ttk.Label(metrics, textvariable=self.money_in_var).pack(side="left", padx=10)
        ttk.Label(metrics, textvariable=self.money_out_var).pack(side="left", padx=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.depositors_text = self._add_tab("Recurring Depositors")
        self.alerts_text = self._add_tab("Missing Payments")
        self.categories_text = self._add_tab("Spending by Category")
        self.preview_text = self._add_tab("Transactions")

        export = ttk.Frame(self.root, padding=10)
        export.pack(fill="x")
        ttk.Button(export, text="Export JSON", command=self._export_json).pack(side="left", padx=6)
        ttk.Button(export, text="Export Markdown", command=self._export_md).pack(side="left", padx=6)

    def _add_tab(self, title: str) -> ttk.Text:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        text = ttk.Text(frame, wrap="word")
        text.pack(fill="both", expand=True)
        return text

    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select bank statement",
            filetypes=[
                ("Supported files", "*.csv *.xlsx *.xls *.pdf"),
                ("CSV", "*.csv"),
                ("Excel", "*.xlsx *.xls"),
                ("PDF", "*.pdf"),
            ],
        )
        if not path:
            return
        self.tmp_path = path
        self.file_label.config(text=Path(path).name)

    def _analyse(self) -> None:
        if not self.tmp_path:
            messagebox.showwarning("jjbank", "Select a statement file first.")
            return

        password = self.password_var.get() or None
        suffix = Path(self.tmp_path).suffix.lower()
        if suffix == ".pdf" and not password:
            messagebox.showwarning("jjbank", "Enter the PDF password, then Analyse again.")
            return

        try:
            statement = normalise_statement(self.tmp_path, password=password)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("jjbank", f"Failed to read statement: {exc}")
            return

        if statement.empty:
            messagebox.showinfo("jjbank", "No transactions could be parsed.")
            return

        self.rows = statement.to_dict(orient="records")
        self.report = build_report(self.rows)
        self._render()

    def _render(self) -> None:
        money = self.report.get("money_in_out", {})
        self.money_in_var.set(f"Money In: {money.get('total_in', 0):.2f}")
        self.money_out_var.set(f"Money Out: {money.get('total_out', 0):.2f}")

        income = self.report.get("income_analysis", {})
        depositors = income.get("monthly_depositors", [])
        alerts = income.get("alerts", [])

        self.depositors_text.delete("1.0", "end")
        self.depositors_text.insert("end", "\n".join(depositors) if depositors else "None detected")

        self.alerts_text.delete("1.0", "end")
        if alerts:
            lines = [f"{alert['name']} missing in {alert['month']}" for alert in alerts]
            self.alerts_text.insert("end", "\n".join(lines))
        else:
            self.alerts_text.insert("end", "No missing payments detected.")

        spend = self.report.get("spending_summary", {})
        categories = spend.get("categories", {})
        lines = []
        for cat, amt in sorted(categories.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"{cat}: {amt:.2f}")
        lines.append(f"Total Out: {spend.get('total_out', 0):.2f}")
        self.categories_text.delete("1.0", "end")
        self.categories_text.insert("end", "\n".join(lines) if categories else "No spending data available.")

        self.preview_text.delete("1.0", "end")
        for row in self.rows[:200]:
            self.preview_text.insert(
                "end", f"{row.get('date','')} | {row.get('description','')} | {row.get('amount',0):.2f} | {row.get('side','')}\n"
            )
        if len(self.rows) > 200:
            self.preview_text.insert("end", f"\n... {len(self.rows) - 200} more rows")

    def _export_json(self) -> None:
        if not self.report:
            messagebox.showinfo("jjbank", "Run analysis first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        Path(path).write_text(json.dumps(self.report, indent=2), encoding="utf-8")
        messagebox.showinfo("jjbank", f"Saved JSON to {path}")

    def _export_md(self) -> None:
        if not self.report:
            messagebox.showinfo("jjbank", "Run analysis first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")])
        if not path:
            return
        Path(path).write_text(render_markdown(self.report), encoding="utf-8")
        messagebox.showinfo("jjbank", f"Saved Markdown to {path}")


def main() -> None:
    root = Tk()
    JjBankApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
