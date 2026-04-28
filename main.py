"""
Personal Expense Tracker — CSV Version
======================================
• On launch  → reads all records from expenses.csv (same folder as this script)
• On add     → appends new row to CSV immediately
• On edit    → rewrites CSV with updated row
• On delete  → rewrites CSV without deleted row
• Browse btn → lets you pick a different CSV file at runtime

Run:   python expense_tracker_csv.py
Needs: Python 3.10+  (tkinter + csv ship with Python — no pip needed)
"""

import csv
import os
import uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIES = [
    "Food & Dining", "Transport", "Housing & Rent", "Entertainment",
    "Healthcare", "Shopping", "Education", "Utilities", "Travel", "Other",
]

# Default CSV is placed next to this script — change path here if needed
DEFAULT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.csv")
CSV_FIELDS  = ["id", "date", "category", "amount", "description"]


# ─────────────────────────────────────────────────────────────────────────────
#  DATA MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Expense:
    amount:      float
    category:    str
    description: str
    date:        str          # "YYYY-MM-DD"
    id:          str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_row(self) -> dict:
        """Serialise to a CSV-ready dict (key order matches CSV_FIELDS)."""
        return {
            "id":          self.id,
            "date":        self.date,
            "category":    self.category,
            "amount":      f"{self.amount:.2f}",
            "description": self.description,
        }

    @staticmethod
    def from_row(row: dict) -> "Expense":
        """Deserialise from a csv.DictReader row."""
        return Expense(
            id          = row["id"].strip(),
            date        = row["date"].strip(),
            category    = row["category"].strip(),
            amount      = float(row["amount"].strip()),
            description = row["description"].strip(),
        )


# ─────────────────────────────────────────────────────────────────────────────
#  CSV STORE
#  All persistence lives here — the GUI never touches the file directly.
# ─────────────────────────────────────────────────────────────────────────────

class CSVStore:
    """
    Two-layer store:
        • self._expenses  — in-memory list (fast reads / filtering)
        • self._path      — CSV file on disk (persistent)

    Rules:
        __init__  : ensure file exists → load every row into memory
        add       : append to list → rewrite CSV
        update    : replace in list → rewrite CSV
        delete    : remove from list → rewrite CSV
        load_file : switch to a different CSV path at runtime
    """

    def __init__(self, path: str = DEFAULT_CSV):
        self._path: str = path
        self._expenses: list[Expense] = []
        self._ensure_file()
        self._read_csv()

    # ── File helpers ─────────────────────────────────────────────────────────

    def _ensure_file(self):
        """Create an empty CSV with headers if the file does not exist."""
        if not os.path.exists(self._path):
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            with open(self._path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()

    def _read_csv(self):
        """
        Load every valid row from disk into self._expenses.
        Skips rows that are missing columns or have bad data types —
        so a hand-edited CSV with one bad row won't crash the app.
        """
        self._expenses = []
        try:
            with open(self._path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # Validate that the file actually has the right columns
                if reader.fieldnames and not all(
                    col in reader.fieldnames for col in CSV_FIELDS
                ):
                    raise ValueError(
                        f"CSV missing required columns.\n"
                        f"Expected: {CSV_FIELDS}\n"
                        f"Found:    {reader.fieldnames}"
                    )
                for row in reader:
                    try:
                        self._expenses.append(Expense.from_row(row))
                    except (KeyError, ValueError):
                        # Bad row — skip silently and continue
                        continue
        except FileNotFoundError:
            pass  # _ensure_file should have created it; race condition guard

    def _write_csv(self):
        """
        Overwrite the CSV with the current in-memory list.
        Called after every mutation (add / update / delete).
        Uses a temp file + rename so a crash mid-write never corrupts data.
        """
        tmp = self._path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for e in self._expenses:
                writer.writerow(e.to_row())
        os.replace(tmp, self._path)   # atomic on all major OSes

    # ── Public API ───────────────────────────────────────────────────────────

    def load_file(self, path: str):
        """Switch to a different CSV file and reload data."""
        self._path = path
        self._ensure_file()
        self._read_csv()

    @property
    def path(self) -> str:
        return self._path

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def add(self, expense: Expense) -> Expense:
        self._expenses.append(expense)
        self._write_csv()
        return expense

    def update(self, updated: Expense) -> bool:
        for i, e in enumerate(self._expenses):
            if e.id == updated.id:
                self._expenses[i] = updated
                self._write_csv()
                return True
        return False

    def delete(self, expense_id: str) -> bool:
        before = len(self._expenses)
        self._expenses = [e for e in self._expenses if e.id != expense_id]
        changed = len(self._expenses) < before
        if changed:
            self._write_csv()
        return changed

    def export_copy(self, dest: str):
        """Write a copy of the current data to dest (Export button)."""
        with open(dest, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for e in self._expenses:
                writer.writerow(e.to_row())

    # ── Queries ──────────────────────────────────────────────────────────────

    def all(self) -> list[Expense]:
        return list(self._expenses)

    def filter(
        self,
        category:   Optional[str] = None,
        keyword:    Optional[str] = None,
        start_date: Optional[str] = None,
        end_date:   Optional[str] = None,
    ) -> list[Expense]:
        result = self._expenses
        if category and category != "All":
            result = [e for e in result if e.category == category]
        if keyword:
            kw = keyword.lower()
            result = [e for e in result
                      if kw in e.description.lower() or kw in e.category.lower()]
        if start_date:
            result = [e for e in result if e.date >= start_date]
        if end_date:
            result = [e for e in result if e.date <= end_date]
        return result

    def total(self, expenses: Optional[list[Expense]] = None) -> float:
        return sum(e.amount for e in (expenses if expenses is not None else self._expenses))

    def by_category(self, expenses: Optional[list[Expense]] = None) -> dict[str, float]:
        data = expenses if expenses is not None else self._expenses
        out: dict[str, float] = {}
        for e in data:
            out[e.category] = out.get(e.category, 0) + e.amount
        return dict(sorted(out.items(), key=lambda x: x[1], reverse=True))

    def by_month(self, expenses: Optional[list[Expense]] = None) -> dict[str, float]:
        data = expenses if expenses is not None else self._expenses
        out: dict[str, float] = {}
        for e in data:
            m = e.date[:7]
            out[m] = out.get(m, 0) + e.amount
        return dict(sorted(out.items()))

    def __len__(self):
        return len(self._expenses)


# ─────────────────────────────────────────────────────────────────────────────
#  PALETTE & FONTS
# ─────────────────────────────────────────────────────────────────────────────

BG       = "#0F1117"
SURFACE  = "#1A1D27"
SURFACE2 = "#22263A"
ACCENT   = "#6C63FF"
ACCENT2  = "#FF6584"
GREEN    = "#43D9A2"
YELLOW   = "#F4C842"
TEXT     = "#E8EAF6"
MUTED    = "#7B7F9E"
BORDER   = "#2E3252"
WHITE    = "#FFFFFF"

FN_HEAD = ("Segoe UI", 22, "bold")
FN_LBL  = ("Segoe UI", 10)
FN_MONO = ("Consolas", 10)
FN_SM   = ("Segoe UI", 9)


# ─────────────────────────────────────────────────────────────────────────────
#  SUMMARY POPUP
# ─────────────────────────────────────────────────────────────────────────────

class SummaryWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, store: CSVStore, filtered: list[Expense]):
        super().__init__(parent)
        self.title("Spending Summary")
        self.configure(bg=BG)
        self.geometry("500x570")
        self.resizable(False, False)
        self.grab_set()

        grand_total = store.total(filtered)

        tk.Label(self, text="Spending Summary", font=FN_HEAD,
                 bg=BG, fg=WHITE).pack(pady=(20, 2))
        tk.Label(self,
                 text=f"Total: ₹{grand_total:,.2f}   ({len(filtered)} entries)",
                 font=("Segoe UI", 12, "bold"), bg=BG, fg=GREEN).pack()

        # ── By category ──────────────────────────────────────────────────────
        self._section("By Category")
        cat_card = tk.Frame(self, bg=SURFACE, padx=16, pady=10)
        cat_card.pack(fill="x", padx=20, pady=(0, 6))
        for cat, amt in store.by_category(filtered).items():
            pct = (amt / grand_total * 100) if grand_total else 0
            row = tk.Frame(cat_card, bg=SURFACE)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=cat, bg=SURFACE, fg=TEXT,
                     font=FN_LBL, width=18, anchor="w").pack(side="left")
            c = tk.Canvas(row, bg=SURFACE, height=14, width=120,
                          bd=0, highlightthickness=0)
            c.pack(side="left", padx=(4, 6))
            c.create_rectangle(0, 2, max(2, int(pct * 1.15)), 12,
                               fill=ACCENT, outline="")
            tk.Label(row, text=f"₹{amt:,.0f}  ({pct:.1f}%)",
                     bg=SURFACE, fg=MUTED, font=FN_SM).pack(side="left")

        # ── By month ─────────────────────────────────────────────────────────
        self._section("By Month")
        mon_card = tk.Frame(self, bg=SURFACE, padx=16, pady=10)
        mon_card.pack(fill="x", padx=20, pady=(0, 6))
        for month, amt in sorted(store.by_month(filtered).items(), reverse=True)[:8]:
            row = tk.Frame(mon_card, bg=SURFACE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=month, bg=SURFACE, fg=TEXT,
                     font=FN_MONO, width=9, anchor="w").pack(side="left")
            tk.Label(row, text=f"₹{amt:,.2f}",
                     bg=SURFACE, fg=GREEN, font=FN_MONO).pack(side="left", padx=12)

        tk.Button(self, text="Close", command=self.destroy,
                  bg=SURFACE2, fg=TEXT, relief="flat", font=FN_LBL,
                  cursor="hand2", padx=20, pady=6).pack(pady=16)

    def _section(self, text: str):
        tk.Label(self, text=text, font=("Segoe UI", 11, "bold"),
                 bg=BG, fg=ACCENT).pack(pady=(14, 4))


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

class ExpenseTrackerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Expense Tracker — CSV")
        self.root.geometry("1140x740")
        self.root.minsize(920, 620)
        self.root.configure(bg=BG)

        self.store     = CSVStore()          # reads expenses.csv on startup
        self._edit_id: Optional[str] = None
        self._sort_col = "date"
        self._sort_rev = True

        self._apply_styles()
        self._build_ui()
        self.refresh()                       # populate table from CSV data

    # ── ttk theme ────────────────────────────────────────────────────────────

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, font=FN_LBL,
                    fieldbackground=SURFACE2, bordercolor=BORDER,
                    troughcolor=SURFACE, arrowcolor=MUTED)
        s.configure("Treeview", background=SURFACE, foreground=TEXT,
                    fieldbackground=SURFACE, rowheight=32,
                    font=FN_MONO, borderwidth=0)
        s.configure("Treeview.Heading", background=SURFACE2, foreground=ACCENT,
                    font=("Segoe UI", 10, "bold"), relief="flat")
        s.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", WHITE)])
        s.configure("TCombobox", fieldbackground=SURFACE2, background=SURFACE2,
                    foreground=TEXT, arrowcolor=ACCENT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
        s.map("TCombobox",
              fieldbackground=[("readonly", SURFACE2)],
              selectbackground=[("readonly", SURFACE2)],
              selectforeground=[("readonly", TEXT)])
        s.configure("TScrollbar", background=SURFACE2, troughcolor=SURFACE,
                    arrowcolor=MUTED, bordercolor=BG)

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=14)

        left = tk.Frame(body, bg=BG, width=320)
        left.pack(side="left", fill="y", padx=(0, 16))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_form(left)
        self._build_filter_bar(right)
        self._build_table(right)
        self._build_action_bar(right)

    # ── Header ───────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=SURFACE, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="💸  Expense Tracker",
                 font=FN_HEAD, bg=SURFACE, fg=WHITE).pack(
            side="left", padx=24, pady=10)

        # ── CSV file indicator + Browse button ───────────────────────────────
        csv_bar = tk.Frame(hdr, bg=SURFACE)
        csv_bar.pack(side="left", padx=4)

        tk.Label(csv_bar, text="📂", font=FN_SM, bg=SURFACE, fg=YELLOW).pack(
            side="left")
        self.csv_path_lbl = tk.Label(
            csv_bar,
            text=self._short_path(self.store.path),
            font=FN_SM, bg=SURFACE, fg=YELLOW, cursor="hand2"
        )
        self.csv_path_lbl.pack(side="left", padx=(2, 8))
        self.csv_path_lbl.bind("<Button-1>",
                               lambda _: self._show_full_path())

        self._btn(csv_bar, "Browse CSV", self._browse_csv,
                  color=SURFACE2).pack(side="left", ipady=2, ipadx=4)

        self.total_lbl = tk.Label(hdr, text="",
                                  font=("Segoe UI", 13, "bold"),
                                  bg=SURFACE, fg=GREEN)
        self.total_lbl.pack(side="right", padx=24)

    # ── Add / Edit form ──────────────────────────────────────────────────────

    def _build_form(self, parent):
        card = tk.Frame(parent, bg=SURFACE)
        card.pack(fill="both", expand=True)
        self._card_title(card, "➕  Add / Edit Expense")

        def lbl(text):
            return tk.Label(card, text=text, bg=SURFACE, fg=MUTED,
                            font=FN_SM, anchor="w")

        def entry(var):
            e = tk.Entry(card, textvariable=var,
                         bg=SURFACE2, fg=TEXT, insertbackground=ACCENT,
                         relief="flat", font=FN_LBL, bd=0,
                         highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=ACCENT)
            e.pack(fill="x", padx=16, pady=(0, 10), ipady=6)
            return e

        lbl("Amount (₹)").pack(fill="x", padx=16, pady=(14, 2))
        self.var_amt = tk.StringVar()
        entry(self.var_amt)

        lbl("Category").pack(fill="x", padx=16, pady=(0, 2))
        self.var_cat = tk.StringVar(value=CATEGORIES[0])
        ttk.Combobox(card, textvariable=self.var_cat,
                     values=CATEGORIES, state="readonly",
                     font=FN_LBL).pack(fill="x", padx=16, pady=(0, 10), ipady=5)

        lbl("Description").pack(fill="x", padx=16, pady=(0, 2))
        self.var_desc = tk.StringVar()
        entry(self.var_desc)

        lbl("Date (YYYY-MM-DD)").pack(fill="x", padx=16, pady=(0, 2))
        self.var_date = tk.StringVar(value=str(date.today()))
        entry(self.var_date)

        btn_row = tk.Frame(card, bg=SURFACE)
        btn_row.pack(fill="x", padx=16, pady=(6, 10))
        self._btn(btn_row, "💾  Save",  self._save).pack(
            side="left", fill="x", expand=True, padx=(0, 6), ipady=7)
        self._btn(btn_row, "✖  Clear", self._clear_form, SURFACE2).pack(
            side="left", fill="x", expand=True, ipady=7)

        self.err_lbl = tk.Label(card, text="", bg=SURFACE, fg=ACCENT2,
                                font=FN_SM, wraplength=270, justify="left")
        self.err_lbl.pack(fill="x", padx=16, pady=(0, 4))

        self.edit_lbl = tk.Label(card, text="", bg=SURFACE, fg=ACCENT,
                                 font=FN_SM)
        self.edit_lbl.pack(fill="x", padx=16, pady=(0, 8))

        # ── Info box ─────────────────────────────────────────────────────────
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16)
        tk.Label(
            card,
            text=(
                "✅  Every change is saved to the CSV instantly.\n"
                "🔄  Reopen the app to reload from the same file."
            ),
            bg=SURFACE, fg=MUTED, font=FN_SM,
            justify="left", wraplength=270,
        ).pack(fill="x", padx=16, pady=10)

    # ── Filter bar ───────────────────────────────────────────────────────────

    def _build_filter_bar(self, parent):
        bar = tk.Frame(parent, bg=SURFACE, pady=8)
        bar.pack(fill="x", pady=(0, 10))

        def lbl(t, w=None):
            kw = dict(bg=SURFACE, fg=MUTED, font=FN_SM)
            if w:
                kw["width"] = w
            return tk.Label(bar, text=t, **kw)

        def mini(var, w=11):
            return tk.Entry(bar, textvariable=var,
                            bg=SURFACE2, fg=TEXT, insertbackground=ACCENT,
                            relief="flat", font=FN_LBL, width=w,
                            highlightthickness=1,
                            highlightbackground=BORDER,
                            highlightcolor=ACCENT)

        lbl("Category", 8).pack(side="left", padx=(14, 2))
        self.fil_cat = tk.StringVar(value="All")
        ttk.Combobox(bar, textvariable=self.fil_cat,
                     values=["All"] + CATEGORIES,
                     state="readonly", font=FN_LBL,
                     width=15).pack(side="left", padx=(0, 10))

        lbl("Search", 7).pack(side="left", padx=(0, 2))
        self.fil_kw = tk.StringVar()
        mini(self.fil_kw, 16).pack(side="left", ipady=4, padx=(0, 10))

        lbl("From", 4).pack(side="left", padx=(0, 2))
        self.fil_from = tk.StringVar()
        mini(self.fil_from).pack(side="left", ipady=4, padx=(0, 6))

        lbl("To", 3).pack(side="left", padx=(0, 2))
        self.fil_to = tk.StringVar()
        mini(self.fil_to).pack(side="left", ipady=4, padx=(0, 10))

        self._btn(bar, "Apply",  self.refresh,        width=8).pack(
            side="left", ipady=4, padx=(0, 6))
        self._btn(bar, "Reset",  self._reset_filters, SURFACE2, width=8).pack(
            side="left", ipady=4)

    # ── Treeview ─────────────────────────────────────────────────────────────

    def _build_table(self, parent):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True)

        COLS   = ("ID", "Date", "Category", "Amount", "Description")
        WIDTHS = {"ID": 80, "Date": 105, "Category": 158,
                  "Amount": 108, "Description": 330}

        self.tree = ttk.Treeview(frame, columns=COLS,
                                 show="headings", selectmode="browse")
        for c in COLS:
            self.tree.heading(c, text=c,
                              command=lambda _c=c: self._toggle_sort(_c))
            self.tree.column(c, width=WIDTHS[c], anchor="w")

        vsb = ttk.Scrollbar(frame, orient="vertical",
                             command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("odd",  background=SURFACE)
        self.tree.tag_configure("even", background=SURFACE2)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    # ── Action bar ───────────────────────────────────────────────────────────

    def _build_action_bar(self, parent):
        bar = tk.Frame(parent, bg=SURFACE, pady=8)
        bar.pack(fill="x", pady=(10, 0))

        self._btn(bar, "🗑  Delete",     self._delete_selected, ACCENT2).pack(
            side="left", padx=12, ipady=5, ipadx=4)
        self._btn(bar, "📊  Summary",    self._open_summary,    ACCENT).pack(
            side="left", ipady=5, ipadx=4)
        self._btn(bar, "📤  Export CSV", self._export_copy,     SURFACE2).pack(
            side="left", ipady=5, ipadx=4, padx=(8, 0))

        self.count_lbl = tk.Label(bar, text="", font=FN_SM, bg=SURFACE, fg=MUTED)
        self.count_lbl.pack(side="right", padx=16)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _card_title(self, parent: tk.Frame, text: str):
        tk.Label(parent, text=text, bg=SURFACE, fg=ACCENT,
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(
            fill="x", padx=16, pady=(14, 6))
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16)

    def _btn(self, parent, text: str, cmd, color=ACCENT, width=None):
        kw = dict(text=text, command=cmd, bg=color, fg=WHITE,
                  relief="flat", cursor="hand2", font=FN_LBL,
                  activebackground=ACCENT, activeforeground=WHITE,
                  bd=0, padx=10)
        if width:
            kw["width"] = width
        return tk.Button(parent, **kw)

    def _set_error(self, msg: str):
        self.err_lbl.config(text=msg)

    @staticmethod
    def _short_path(path: str, max_len: int = 45) -> str:
        """Truncate a long path for display in the header."""
        return path if len(path) <= max_len else "…" + path[-(max_len - 1):]

    # ── CSV file management ──────────────────────────────────────────────────

    def _browse_csv(self):
        """
        Let the user pick any CSV file.
        If the chosen file already has the right columns → load it.
        If it's empty / new → the store will initialise it with headers.
        """
        chosen = filedialog.askopenfilename(
            title="Select an expenses CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.path.dirname(self.store.path),
        )
        if not chosen:
            return
        try:
            self.store.load_file(chosen)
            self.csv_path_lbl.config(text=self._short_path(chosen))
            self.root.title(f"Expense Tracker — {os.path.basename(chosen)}")
            self._clear_form()
            self.refresh()
            messagebox.showinfo(
                "File loaded",
                f"Loaded {len(self.store)} record(s) from:\n{chosen}"
            )
        except ValueError as err:
            messagebox.showerror("Invalid CSV", str(err))
        except Exception as err:
            messagebox.showerror("Error", f"Could not load file:\n{err}")

    def _show_full_path(self):
        messagebox.showinfo("CSV file location",
                            f"Currently reading & writing to:\n\n{self.store.path}")

    def _export_copy(self):
        """Save a copy of the current data to any user-chosen location."""
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export a copy of expenses",
            initialfile="expenses_export.csv",
        )
        if dest:
            self.store.export_copy(dest)
            messagebox.showinfo("Exported",
                                f"Data exported to:\n{dest}")

    # ── Form CRUD actions ────────────────────────────────────────────────────

    def _save(self):
        """Validate form → add or update record → write CSV → refresh table."""
        self._set_error("")
        amt_raw  = self.var_amt.get().strip()
        desc     = self.var_desc.get().strip()
        cat      = self.var_cat.get()
        date_str = self.var_date.get().strip()

        # Validation
        if not amt_raw:
            self._set_error("Amount is required."); return
        try:
            amt = float(amt_raw)
            if amt <= 0:
                raise ValueError
        except ValueError:
            self._set_error("Amount must be a positive number."); return
        if not desc:
            self._set_error("Description is required."); return
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self._set_error("Date must be YYYY-MM-DD."); return

        # Persist — CSVStore writes the file immediately after each call
        if self._edit_id:
            self.store.update(
                Expense(id=self._edit_id, amount=amt, category=cat,
                        description=desc, date=date_str)
            )
        else:
            self.store.add(
                Expense(amount=amt, category=cat,
                        description=desc, date=date_str)
            )

        self._clear_form()
        self.refresh()

    def _clear_form(self):
        self.var_amt.set("")
        self.var_desc.set("")
        self.var_cat.set(CATEGORIES[0])
        self.var_date.set(str(date.today()))
        self._edit_id = None
        self._set_error("")
        self.edit_lbl.config(text="")

    def _on_row_select(self, _event=None):
        """Load selected row into the form for editing."""
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        # Column order: ID | Date | Category | Amount | Description
        self._edit_id = vals[0]
        self.var_date.set(vals[1])
        self.var_cat.set(vals[2])
        self.var_amt.set(vals[3])
        self.var_desc.set(vals[4])
        self.edit_lbl.config(text=f"✏  Editing  #{vals[0]}")
        self._set_error("")

    def _delete_selected(self):
        """Delete selected row from memory + CSV."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing selected",
                                "Click a row in the table first.")
            return
        vals = self.tree.item(sel[0], "values")
        if messagebox.askyesno(
            "Confirm Delete",
            f"Permanently delete this entry from the CSV?\n\n"
            f"  ID: {vals[0]}\n"
            f"  {vals[1]}  |  {vals[2]}\n"
            f"  ₹{vals[3]}  |  {vals[4]}"
        ):
            self.store.delete(vals[0])   # updates CSV immediately
            self._clear_form()
            self.refresh()

    # ── Filters & sorting ────────────────────────────────────────────────────

    def _reset_filters(self):
        self.fil_cat.set("All")
        self.fil_kw.set("")
        self.fil_from.set("")
        self.fil_to.set("")
        self.refresh()

    def _get_filtered(self) -> list[Expense]:
        return self.store.filter(
            category   = self.fil_cat.get() or None,
            keyword    = self.fil_kw.get().strip() or None,
            start_date = self.fil_from.get().strip() or None,
            end_date   = self.fil_to.get().strip() or None,
        )

    def _toggle_sort(self, col: str):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = col in ("date", "amount")
        self.refresh()

    # ── Summary ──────────────────────────────────────────────────────────────

    def _open_summary(self):
        filtered = self._get_filtered()
        if not filtered:
            messagebox.showinfo("No data",
                                "No expenses match the current filters.")
            return
        SummaryWindow(self.root, self.store, filtered)

    # ── Refresh table ────────────────────────────────────────────────────────

    def refresh(self):
        """Re-read filtered+sorted data from the store and repopulate the table."""
        expenses = self._get_filtered()

        attr_map = {
            "ID": "id", "Date": "date", "Category": "category",
            "Amount": "amount", "Description": "description",
        }
        expenses.sort(
            key=lambda e: getattr(e, attr_map.get(self._sort_col, "date")),
            reverse=self._sort_rev,
        )

        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, e in enumerate(expenses):
            self.tree.insert("", "end", values=(
                e.id, e.date, e.category,
                f"{e.amount:,.2f}", e.description,
            ), tags=("even" if i % 2 == 0 else "odd",))

        total = self.store.total(expenses)
        self.total_lbl.config(text=f"Total: ₹{total:,.2f}")
        n, N = len(expenses), len(self.store)
        self.count_lbl.config(
            text=f"{n} of {N} entr{'y' if N == 1 else 'ies'} shown"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app  = ExpenseTrackerApp(root)
    root.mainloop()