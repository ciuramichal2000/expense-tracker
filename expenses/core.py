"""Personal expense tracker on SQLite: amounts in integer grosze/cents, categories, monthly summaries, budgets with warnings and a text bar chart."""
import datetime as dt
import sqlite3
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List


def to_cents(amount) -> int:
    return int((Decimal(str(amount).replace(",", ".")) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def fmt(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    return "%s%d.%02d" % (sign, abs(cents) // 100, abs(cents) % 100)


class Tracker:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path)
        self.db.executescript("CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY, day TEXT NOT NULL, cents INTEGER NOT NULL CHECK(cents > 0), category TEXT NOT NULL, note TEXT);"
                              "CREATE TABLE IF NOT EXISTS budgets(category TEXT PRIMARY KEY, cents INTEGER NOT NULL);")

    def add(self, day: str, amount, category: str, note: str = "") -> int:
        dt.date.fromisoformat(day)                           # reject impossible dates
        cents = to_cents(amount)
        if cents <= 0:
            raise ValueError("amount must be positive")
        cur = self.db.execute("INSERT INTO expenses(day,cents,category,note) VALUES(?,?,?,?)", (day, cents, category.strip().lower(), note))
        self.db.commit()
        return cur.lastrowid

    def delete(self, expense_id: int) -> bool:
        cur = self.db.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        self.db.commit()
        return cur.rowcount == 1

    def month(self, ym: str) -> List[dict]:
        return [{"id": i, "day": d, "cents": c, "category": cat, "note": n} for i, d, c, cat, n in
                self.db.execute("SELECT id, day, cents, category, note FROM expenses WHERE day LIKE ? ORDER BY day, id", (ym + "-%",))]

    def summary(self, ym: str) -> Dict[str, int]:
        rows = self.db.execute("SELECT category, SUM(cents) s FROM expenses WHERE day LIKE ? GROUP BY category ORDER BY s DESC, category", (ym + "-%",))
        return {c: s for c, s in rows}

    def set_budget(self, category: str, amount) -> None:
        self.db.execute("INSERT OR REPLACE INTO budgets VALUES(?,?)", (category.strip().lower(), to_cents(amount)))
        self.db.commit()

    def budget_status(self, ym: str, warn_at: float = 0.8) -> List[dict]:
        spent = self.summary(ym)
        out = []
        for cat, limit in self.db.execute("SELECT category, cents FROM budgets ORDER BY category"):
            s = spent.get(cat, 0)
            state = "over" if s > limit else "warning" if s >= limit * warn_at else "ok"
            out.append({"category": cat, "spent": s, "limit": limit, "state": state})
        return out

    def chart(self, ym: str, width: int = 30) -> str:
        data = self.summary(ym)
        if not data:
            return "no expenses in %s" % ym
        top = max(data.values())
        return "\n".join("%-12s %s %s" % (c, "#" * max(1, round(v / top * width)), fmt(v)) for c, v in data.items())
