# expense-tracker

A personal expense tracker on SQLite. Amounts are stored as **integer cents** (parsed from `12,34` or `12.34`, rounded half up), so sums never drift. Monthly summaries by category sorted by size, budgets per category with `ok` / `warning` (80%) / `over` states, delete, and a text bar chart.

`python -m pytest` runs the tests. Pure Python standard library; built with AI coding assistance.
