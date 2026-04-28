# 💸 Personal Expense Tracker

A lightweight, fully offline personal expense tracker built with **Python**, **Tkinter**, and **CSV** — no database, no internet, no pip installs required.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange)
![Storage](https://img.shields.io/badge/Storage-CSV-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📸 Features

| Feature | Details |
|---|---|
| ➕ Add / Edit / Delete | Full CRUD via a clean dark-themed UI |
| 💾 Auto-save to CSV | Every change is written to disk instantly |
| 🔄 Persistent on reload | Records are loaded from CSV every time the app opens |
| 📂 Browse CSV | Switch to any CSV file at runtime via a file picker |
| 🔍 Filter | By category, keyword search, and date range |
| 🔃 Sort | Click any column header to sort ascending / descending |
| 📊 Summary popup | Category bar chart + monthly spending breakdown |
| 📤 Export | Save a copy of your data to any location |
| 🌑 Dark UI | Purple accent theme with ₹ currency formatting |

---

## 🗂 Project Structure

```
expense-tracker/
├── expense_tracker_csv.py   ← Main app — run this
├── expenses.csv             ← Auto-created on first run (your data lives here)
└── README.md
```

> All logic lives in a single Python file — no packages, no folders to manage.

---

## 🚀 Getting Started

### Prerequisites

- Python **3.10 or higher**
- `tkinter` — ships with Python on Windows and macOS. On Linux, install it with:

```bash
sudo apt install python3-tk      # Debian / Ubuntu
sudo dnf install python3-tkinter # Fedora
```

### Run the app

```bash
# Clone the repo
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker

# Launch
python expense_tracker_csv.py
```

That's it. No `pip install` needed.

---

## 📄 CSV Format

Data is stored in `expenses.csv` in the same folder as the script. The file is created automatically on first launch. You can also hand-edit it in Excel or Google Sheets — just keep the column order intact.

```csv
id,date,category,amount,description
a1b2c3d4,2025-04-01,Food & Dining,320.00,Lunch at cafe
b2c3d4e5,2025-04-02,Transport,1200.00,Monthly metro pass
c3d4e5f6,2025-04-03,Entertainment,499.00,Netflix subscription
```

| Column | Type | Example |
|---|---|---|
| `id` | 8-char hex string (auto-generated) | `a1b2c3d4` |
| `date` | `YYYY-MM-DD` | `2025-04-18` |
| `category` | One of the 10 built-in categories | `Transport` |
| `amount` | Decimal number | `320.00` |
| `description` | Free text | `Lunch at cafe` |

### Available Categories

`Food & Dining` · `Transport` · `Housing & Rent` · `Entertainment` · `Healthcare` · `Shopping` · `Education` · `Utilities` · `Travel` · `Other`

---

## 🧠 How It Works

```
┌──────────────────────────────────────────────┐
│              ExpenseTrackerApp (GUI)          │
│  Form → validates input → calls CSVStore     │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│                 CSVStore                     │
│  • Reads CSV on startup into a Python list   │
│  • After every add / edit / delete:          │
│    writes the full list back to disk (safe   │
│    atomic write via temp file + os.replace)  │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
            expenses.csv  (on disk)
```

---

## 🖥 App Walkthrough

### Adding an expense
1. Fill in **Amount**, **Category**, **Description**, and **Date** in the left panel
2. Click **💾 Save** — the row appears in the table and is written to `expenses.csv` immediately

### Editing an expense
1. Click any row in the table — fields are loaded into the form automatically
2. Make your changes and click **💾 Save**

### Deleting an expense
1. Click a row to select it
2. Click **🗑 Delete** and confirm — the row is removed from the CSV instantly

### Switching CSV files
- Click **Browse CSV** in the header to load any other `.csv` file
- The app validates the file's columns before loading

### Viewing a summary
- Click **📊 Summary** to open a popup showing spending by category (with bar charts) and by month

---

## 🔒 Data Safety

- Writes use a **temp file + atomic rename** (`os.replace`) — a crash mid-write will never corrupt your CSV
- The original `expenses.csv` is never partially overwritten

---

## 🛠 Customisation

**Change the default CSV path** — edit line near the top of the file:
```python
DEFAULT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.csv")
```

**Add or remove categories** — edit the `CATEGORIES` list:
```python
CATEGORIES = [
    "Food & Dining", "Transport", "Housing & Rent", ...
]
```

**Change currency symbol** — search for `₹` in the file and replace with your symbol (e.g. `$`, `€`, `£`)

---

## 🗺 Roadmap

- [ ] Charts with `matplotlib` (pie chart for categories, bar chart for monthly trends)
- [ ] Recurring expenses (auto-add monthly entries)
- [ ] Budget limits per category with alerts
- [ ] Multi-currency support
- [ ] Light theme toggle

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/add-charts`)
3. Commit your changes (`git commit -m 'Add matplotlib charts'`)
4. Push to the branch (`git push origin feature/add-charts`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

Built with Python's standard library only — `tkinter`, `csv`, `dataclasses`, `uuid`, `os`, `datetime`.
No external dependencies.
