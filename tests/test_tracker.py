import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from expenses import Tracker, fmt, to_cents  # noqa: E402


def test_amounts_become_exact_integer_cents():
    assert to_cents("12,34") == 1234 and to_cents(0.1) == 10 and to_cents("19.999") == 2000 and to_cents(5) == 500
    assert fmt(1205) == "12.05" and fmt(5) == "0.05" and fmt(-250) == "-2.50"
    assert sum(to_cents("0.10") for _ in range(10)) == 100          # no floating point drift


def test_add_validates_amount_and_date_and_normalises_category():
    t = Tracker()
    t.add("2024-03-05", "10,50", " Food ")
    assert t.month("2024-03")[0]["category"] == "food"
    with pytest.raises(ValueError):
        t.add("2024-03-05", 0, "x")
    with pytest.raises(ValueError):
        t.add("2024-02-30", 5, "x")


def test_monthly_summary_is_sorted_by_amount_and_limited_to_the_month():
    t = Tracker()
    for day, amt, cat in [("2024-03-01", 50, "food"), ("2024-03-09", 120, "rent"), ("2024-03-12", 30.5, "food"), ("2024-04-01", 999, "food")]:
        t.add(day, amt, cat)
    assert t.summary("2024-03") == {"rent": 12000, "food": 8050}
    assert list(t.summary("2024-03")) == ["rent", "food"] and t.summary("2024-05") == {}


def test_budget_states_ok_warning_over():
    t = Tracker()
    t.set_budget("food", 100)
    t.set_budget("fun", 50)
    t.set_budget("rent", 500)
    t.add("2024-03-01", 85, "food")
    t.add("2024-03-02", 60, "fun")
    t.add("2024-03-03", 10, "rent")
    states = {b["category"]: b["state"] for b in t.budget_status("2024-03")}
    assert states == {"food": "warning", "fun": "over", "rent": "ok"}


def test_delete_and_chart():
    t = Tracker()
    a = t.add("2024-03-01", 100, "rent")
    t.add("2024-03-02", 25, "food")
    chart = t.chart("2024-03", width=20).splitlines()
    assert chart[0].startswith("rent") and chart[0].count("#") == 20 and chart[1].count("#") == 5
    assert t.delete(a) and not t.delete(a)
    assert t.chart("2024-04") == "no expenses in 2024-04"
