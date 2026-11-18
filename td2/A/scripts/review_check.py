"""Pair A cross-review checks (TD 2). Read-only, no network, no model call.

  part B: re-runs the C10 queries and the delta of pair B on the shop database
  part C: recomputes the per-family rates, the HTTP 429 cells and the token medians of pair C

Usage from the repository root:
  python3 td2/A/scripts/review_check.py --db <student-kit-dir>/data/boutique.sqlite
"""
import argparse
import csv
import sqlite3
import statistics

parser = argparse.ArgumentParser()
parser.add_argument("--db", required = True)
parser.add_argument("--traces", default = "td1/data/traces/traces-td1.csv")
args = parser.parse_args()

connection = sqlite3.connect("file:" + args.db + "?mode=ro", uri = True)
JOINS = "FROM orders o JOIN customers c ON c.customer_id = o.customer_id JOIN product p ON p.product_id = o.product_id"
CASE_A = ("CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER) = 25 "
          "AND strftime('%m-%d', o.date) >= strftime('%m-%d', c.birth_date)")

print("=== PART B: pair B, wrong consensus on C10 ===")
reference_value = connection.execute("SELECT SUM(o.quantity_product * p.price) " + JOINS + " WHERE date(o.date) >= date(c.birth_date, '+25 years') AND date(o.date) < date(c.birth_date, '+26 years')").fetchone()[0]
case_a_value = connection.execute("SELECT SUM(o.quantity_product * p.price) " + JOINS + " WHERE " + CASE_A).fetchone()[0]
print("reference window:", reference_value, "(expected 558980)")
print("case (a) only, the shared faulty clause:", case_a_value, "(expected 119410)")
qwen_branch_lines = connection.execute("SELECT COUNT(*) " + JOINS + " WHERE (strftime('%Y', o.date) - strftime('%Y', c.birth_date)) = 24 AND (strftime('%m', o.date) || strftime('%d', o.date)) < (strftime('%m', c.birth_date) || strftime('%d', c.birth_date))").fetchone()[0]
print("order lines matched by Qwen's '= 24' branch:", qwen_branch_lines, "(expected 0)")
delta_rows = connection.execute("SELECT c.customer_id, c.birth_date, COUNT(*), SUM(o.quantity_product * p.price) " + JOINS
    + " WHERE c.birth_date > date(o.date, '-26 years') AND c.birth_date <= date(o.date, '-25 years') AND NOT (" + CASE_A + ") GROUP BY c.customer_id, c.birth_date ORDER BY c.customer_id").fetchall()
for delta_row in delta_rows:
    print("  delta:", delta_row)
print("delta total:", sum(row[3] for row in delta_rows), "in", sum(row[2] for row in delta_rows), "lines | reference - case (a):", reference_value - case_a_value)
wrongly_added = connection.execute("SELECT COUNT(*) " + JOINS + " WHERE NOT (c.birth_date > date(o.date, '-26 years') AND c.birth_date <= date(o.date, '-25 years')) AND " + CASE_A).fetchone()[0]
print("lines counted by the faulty clause but not by the reference (wrongly added):", wrongly_added, "(expected 0)")
python_total = python_year26 = 0
for birth_date, order_date, quantity, price in connection.execute("SELECT c.birth_date, o.date, o.quantity_product, p.price " + JOINS):
    birth_year, birth_month, birth_day = int(birth_date[:4]), int(birth_date[5:7]), int(birth_date[8:10])
    order_year, order_month, order_day = int(order_date[:4]), int(order_date[5:7]), int(order_date[8:10])
    completed_age = order_year - birth_year - (1 if (order_month, order_day) < (birth_month, birth_day) else 0)
    if completed_age == 25:
        python_total += quantity * price
        if order_year - birth_year == 26:
            python_year26 += quantity * price
print("independent Python age-25 revenue:", python_total, "| of which year difference 26:", python_year26)

print()
print("=== PART C: pair C, rates and measured facts ===")
all_rows = list(csv.DictReader(open(args.traces)))
last_attempt = {}
for row in all_rows:
    last_attempt[(row["model_requested"], row["case_id"])] = row
families = {"F1": ["C01", "C04", "C05", "C06", "C07", "C20"], "F2": ["C02", "C08", "C09", "C11"], "F2b": ["C10"], "F3": ["C03", "C12", "C13", "C14"], "F4": ["C15", "C16", "C17", "C18", "C19"]}
models = [("gpt-oss-120b", "openai/gpt-oss-120b"), ("gpt-oss-20b", "openai/gpt-oss-20b"), ("cohere", "cohere/north-mini-code:free"), ("qwen3.8-27b", "qwen/qwen3.8-27b"), ("dots", "dots-studio/dots-3-note-preview:free")]
claimed = {"F1": [6, 6, 6, 6, 6], "F2": [4, 2, 0, 4, 2], "F2b": [1, 1, 0, 0, 0], "F3": [4, 4, 4, 3, 4], "F4": [4, 5, 3, 2, 3]}
mismatches = 0
for family, cases in families.items():
    computed = [sum(1 for case in cases if last_attempt[(model, case)]["verdict"] == "correct") for _, model in models]
    print(family, "computed", computed, "of", len(cases), "| claimed by pair C", claimed[family], "| same:", computed == claimed[family])
    mismatches += 0 if computed == claimed[family] else 1
print("family rate mismatches:", mismatches)
rows_429 = [(row["model_requested"], row["case_id"]) for row in all_rows if row["http_status"] == "429"]
print("HTTP 429 rows:", rows_429)
cells = list(last_attempt.values())
print("final cells:", len(cells), "| median prompt tokens:", statistics.median(float(row["tokens_prompt"]) for row in cells), "| median completion tokens:", statistics.median(float(row["tokens_completion"]) for row in cells))
with_reasoning = [row for row in all_rows if row["tokens_reasoning"] not in ("", None) and float(row["tokens_reasoning"]) > 0]
print("rows with a reasoning counter > 0:", len(with_reasoning), "| completion >= reasoning on all:", all(float(row["tokens_completion"]) >= float(row["tokens_reasoning"]) for row in with_reasoning))
for label, input_price, output_price in [("gpt-oss-20b at 0.075 / 0.30 USD per million", 0.075, 0.30), ("gpt-oss-120b at 0.15 / 0.60 USD per million", 0.15, 0.60)]:
    print("price per request,", label, ":", round((626 * input_price + 140 * output_price) / 1e6, 7))
