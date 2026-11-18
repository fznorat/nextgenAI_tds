#!/usr/bin/env python3
"""TD 2, step 3 (pair C): the deterministic check the routing rule calls `reference`.

The rule sends every age question, and every payout, to a check that does not
depend on a vote. This script is that check, executed: for one question it
rebuilds the reference query from the question's own parameters, runs it on the
read-only database, and compares a candidate value with it.

Why the rule needs this rather than a quorum: on C10 three of our five models
return 119410 instead of 558980, so the fixed 2-of-3 panel and the 3-of-5 quorum
both return a wrong value (see td2/C/td2/C/analysis/csv/quorum-by-family-td1.csv). A check
that is a second opinion cannot catch an error the panel shares; a check that
recomputes the answer from the question can.

The window used for a completed age of 25 on date D is the one fixed by the
protocol, written once here and parameterised:

    c.birth_date >  date(D, '-26 years')   AND   c.birth_date <= date(D, '-25 years')

with D = the reference date of the question, or `o.date` when the question asks
for the age at the time of the order.

    python3 td2/C/scripts/age_guard_td2.py <kit_dir>
    python3 td2/C/scripts/age_guard_td2.py <kit_dir> --case C10 --candidate 119410
    python3 td2/C/scripts/age_guard_td2.py <kit_dir> --quorum td2/C/analysis/csv/quorum-by-family-td1.csv

`<kit_dir>` is the student kit holding `data/boutique.sqlite`; the database is
not committed to this repository. The connection is opened read-only.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

PAIR_C = Path(__file__).resolve().parents[1]
REFERENCE = PAIR_C.parents[1] / "td1" / "data" / "references" / "reference-td1.csv"
QUORUM = PAIR_C / "analysis" / "csv" / "quorum-by-family-td1.csv"

# The twenty questions, as parameters rather than as SQL text. Source:
# questions-td1-en.md; conventions: period closed on the left, open on the
# right; completed age; revenue = SUM(quantity_product * price) in cents.
QUESTIONS = {
    "C01": {"period": ("2026-03-01", "2026-06-01")},
    "C02": {"age_on": "2026-09-25"},
    "C03": {"products": ("a", "b", "c"), "period": ("2026-01-01", "2026-07-01")},
    "C04": {"period": ("2026-01-01", "2026-10-01")},
    "C05": {"period": ("2026-06-01", "2026-06-02")},
    "C06": {"period": ("2025-01-01", "2026-01-01")},
    "C07": {"period": ("2026-05-31", "2026-06-01")},
    "C08": {"age_on": "2026-09-24"},
    "C09": {"age_on": "2026-09-26"},
    "C10": {"age_at_order": True},
    "C11": {"age_on": "2026-12-01"},
    "C12": {"products": ("a", "b", "c")},
    "C13": {"products": ("a", "c"), "period": ("2026-04-01", "2026-05-01")},
    "C14": {"products": ("a", "b", "c"), "period": ("2026-10-01", "2026-12-01")},
    "C15": {"period": ("2026-03-01", "2026-06-01"), "age_on": "2026-09-25"},
    "C16": {"products": ("a", "b", "c"), "age_on": "2026-09-25"},
    "C17": {"products": ("a", "b", "c"), "period": ("2026-01-01", "2026-07-01"),
            "age_on": "2026-09-25"},
    "C18": {"period": ("2026-05-01", "2026-06-01"), "age_at_order": True},
    "C19": {"products": ("d",), "period": ("2026-09-01", "2026-10-01"),
            "age_on": "2026-09-25"},
    "C20": {"period": ("2026-06-01", "2026-09-01")},
}

AGE = 25


def golden_sql(params: dict) -> tuple[str, list]:
    """Build the reference query of a question from its parameters."""
    where, args = [], []
    if "period" in params:
        start, end = params["period"]
        where.append("o.date >= ? AND o.date < ?")
        args += [f"{start} 00:00:00", f"{end} 00:00:00"]
    if "products" in params:
        marks = ", ".join("?" for _ in params["products"])
        where.append(f"o.product_id IN ({marks})")
        args += list(params["products"])
    if "age_on" in params:
        # Completed age of exactly AGE on the reference date of the question.
        where.append("c.birth_date > date(?, ?) AND c.birth_date <= date(?, ?)")
        args += [params["age_on"], f"-{AGE + 1} years", params["age_on"], f"-{AGE} years"]
    if params.get("age_at_order"):
        # Same window, but evaluated at the date of each order line.
        where.append("c.birth_date > date(o.date, ?) AND c.birth_date <= date(o.date, ?)")
        args += [f"-{AGE + 1} years", f"-{AGE} years"]
    sql = ("SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents\n"
           "FROM orders o\n"
           "JOIN product p ON p.product_id = o.product_id\n"
           "JOIN customers c ON c.customer_id = o.customer_id\n"
           "WHERE " + "\n  AND ".join(where) if where else
           "SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents\n"
           "FROM orders o\nJOIN product p ON p.product_id = o.product_id\n"
           "JOIN customers c ON c.customer_id = o.customer_id")
    return sql, args


def connect_read_only(kit: Path) -> sqlite3.Connection:
    db = kit / "data" / "boutique.sqlite"
    if not db.exists():
        raise SystemExit(f"database not found: {db}\n"
                         f"pass the student kit directory as the first argument")
    return sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)


def load_csv_column(path: Path, key: str, column: str) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {row[key]: row[column] for row in csv.DictReader(handle)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit", help="student kit directory holding data/boutique.sqlite")
    parser.add_argument("--case", help="check one question only")
    parser.add_argument("--candidate", type=int,
                        help="value in cents a model proposed, to accept or reject")
    parser.add_argument("--quorum", default=str(QUORUM),
                        help="quorum table to confront the check with")
    parser.add_argument("--show-sql", action="store_true", help="print the query used")
    args = parser.parse_args()

    conn = connect_read_only(Path(args.kit))
    reference = {k: int(v) for k, v in
                 load_csv_column(REFERENCE, "case_id", "revenue_cents").items()}
    quorum_values = load_csv_column(Path(args.quorum), "case_id", "quorum_3of5_value")
    panel_values = load_csv_column(Path(args.quorum), "case_id", "panel_2of3_value")

    cases = [args.case] if args.case else list(QUESTIONS)
    disagreements = 0
    print(f"{'case':5s} {'guard':>10s} {'reference':>10s} {'ref ok':7s} "
          f"{'2-of-3':>10s} {'3-of-5':>10s} verdict of the check")
    for case in cases:
        sql, params = golden_sql(QUESTIONS[case])
        if args.show_sql:
            print(f"\n-- {case}\n{sql}\n-- parameters: {params}\n")
        guard = conn.execute(sql, params).fetchone()[0]
        ref = reference.get(case)
        same = "yes" if ref is not None and guard == ref else "NO"
        if same == "NO":
            disagreements += 1

        candidates = []
        if args.candidate is not None:
            candidates.append(("candidate", args.candidate))
        for label, table in (("2-of-3", panel_values), ("3-of-5", quorum_values)):
            raw = table.get(case, "")
            if raw not in ("", None):
                candidates.append((label, int(raw)))
        verdicts = [f"{label} {'accepted' if value == guard else f'REJECTED ({value - guard:+d} cents)'}"
                    for label, value in candidates]
        print(f"{case:5s} {guard:>10d} {str(ref):>10s} {same:7s} "
              f"{panel_values.get(case, 'abstain'):>10s} {quorum_values.get(case, 'abstain'):>10s} "
              f"{'; '.join(verdicts) or 'no candidate'}")

    conn.close()
    if disagreements:
        raise SystemExit(f"\n{disagreements} question(s) where the check disagrees with "
                         f"reference-td1.csv: fix the check before trusting it")
    print(f"\nThe check reproduces the reference on {len(cases)}/{len(cases)} questions, so a "
          f"rejection above is a rejection of the vote, not of the check.")


if __name__ == "__main__":
    main()
