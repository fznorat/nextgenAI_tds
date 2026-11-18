#!/usr/bin/env python3
"""TD 2 - Step 2 (Pair B): wrong consensus on the stored TD 1 traces.

No network. Reads traces-td1.csv, reference-td1.csv and data/boutique.sqlite.

From the repository root (the database is not committed: it is in the student kit):

    python td2/B/scripts/pair_b_wrong_consensus.py --db <student-kit-dir>/data/boutique.sqlite

1. scans every (question, model) cell (last attempt) for shared wrong values;
2. votes: fixed 2-of-3 panel and 3-of-5 quorum (same contract as vote_k_sur_n);
3. C10: runs the 3 faulty SQL + the reference SQL, the delta query (rows missed
   and rows wrongly added) and an independent Python age check;
4. DEMO-VOTE: the one-row toy table (constructed teaching example);
5. cross-check: the same votes recomputed with pair A's Orchestrateur.vote_k_sur_n
   (td2/A/scripts/skeleton-multi-llm-en.py).
"""
import argparse
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
import csv
import sqlite3
from collections import Counter, defaultdict
from datetime import date

PANEL_3 = [("groq", "openai/gpt-oss-120b"),
           ("openrouter", "cohere/north-mini-code:free"),
           ("groq", "qwen/qwen3.8-27b")]


def vote(proposals, k):
    """Same contract as Orchestrateur.vote_k_sur_n. proposals: [(name, value or None)]."""
    n = len(proposals)
    if not (n // 2 < k <= n):
        raise ValueError(f"k={k} is not a strict majority of n={n}")
    names = [p for p, _ in proposals]
    if len(names) != len(set(names)):
        raise ValueError("duplicate (provider, model): a duplicate is not a second vote")
    counts = Counter(v for _, v in proposals if v is not None)
    if counts:
        v, c = counts.most_common(1)[0]
        if c >= k:
            return {"consensus": True, "value": v, "votes": c,
                    "models": [p for p, x in proposals if x == v]}
    return {"consensus": False, "value": None, "votes": max(counts.values(), default=0), "models": []}


def last_attempts(path):
    """Last CSV row per (provider, model, case) = last attempt (as atelier-vote.py does)."""
    last = {}
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["nature"] == "real":
                last[(r["case_id"], r["provider"], r["model_requested"])] = r
    return last


def as_vote(row):
    """Only executed SQL with a value votes; sql_invalid / 429 / not_executed stay in n."""
    if row and row["verdict"] in ("correct", "incorrect") and row["value"] != "":
        return int(row["value"])
    return None


def short(provider, model):
    return model.split("/")[-1]


def scan(last, ref):
    by_case = defaultdict(dict)
    for (q, p, m), r in last.items():
        by_case[q][(p, m)] = r
    print(f"=== Scan: {len(last)} cells (last attempt), {len(by_case)} questions ===")
    found = []
    for q in sorted(by_case):
        wrong = defaultdict(list)
        for pm, r in by_case[q].items():
            if r["verdict"] == "incorrect":
                wrong[int(r["value"])].append(pm)
        for v, pms in wrong.items():
            if len(pms) >= 2:
                found.append((q, v, pms))
    for q, v, pms in found:
        cells = by_case[q]
        p3 = [(f"{p}:{m}", as_vote(cells.get((p, m)))) for p, m in PANEL_3]
        p5 = [(f"{p}:{m}", as_vote(r)) for (p, m), r in sorted(cells.items())]
        v3, v5 = vote(p3, 2), vote(p5, 3)

        def fmt(r):
            if not r["consensus"]:
                return f"ABSTAIN (max {r['votes']} votes)"
            tag = "correct" if r["value"] == ref[q] else "WRONG CONSENSUS"
            return f"{r['value']} ({r['votes']} votes) -> {tag}"
        print(f"\n{q}: shared wrong value {v} by {[short(*x) for x in pms]}  | reference {ref[q]}")
        print("   all 5: " + ", ".join(f"{short(*pm)}={r['verdict']}:{r['value'] or '-'}"
                                      for pm, r in sorted(cells.items())))
        print(f"   2-of-3 panel (120b, Cohere, Qwen) -> {fmt(v3)}")
        print(f"   3-of-5 quorum                      -> {fmt(v5)}")
    return by_case


# ------------------------------------------------------------- C10 SQL evidence
REF_C10 = """SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o JOIN product p ON p.product_id = o.product_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE c.birth_date >  date(o.date, '-26 years')
  AND c.birth_date <= date(o.date, '-25 years')"""

# Condition shared by the 3 faulty queries (Cohere, Qwen first branch, Dots):
#   year(order) - year(birth) = 25 AND month-day(order) >= month-day(birth)
FAULTY_WHERE = """(CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER)) = 25
  AND strftime('%m-%d', o.date) >= strftime('%m-%d', c.birth_date)"""
REF_WHERE = "c.birth_date > date(o.date, '-26 years') AND c.birth_date <= date(o.date, '-25 years')"

DELTA_MISSED = f"""SELECT c.customer_id, c.birth_date,
       COUNT(*) AS order_lines,
       MIN(substr(o.date, 1, 10)) AS first_order, MAX(substr(o.date, 1, 10)) AS last_order,
       SUM(o.quantity_product * p.price) AS revenue_cents_ht
FROM orders o JOIN product p ON p.product_id = o.product_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE ({REF_WHERE})
  AND NOT ({FAULTY_WHERE})
GROUP BY c.customer_id, c.birth_date
ORDER BY c.customer_id"""

DELTA_ADDED = f"""SELECT c.customer_id, SUM(o.quantity_product * p.price) AS revenue_cents_ht
FROM orders o JOIN product p ON p.product_id = o.product_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE ({FAULTY_WHERE})
  AND NOT ({REF_WHERE})
GROUP BY c.customer_id"""

# Qwen's second branch alone (year diff 24, birthday not passed = age 23)
QWEN_BRANCH2 = """SELECT COUNT(*), COALESCE(SUM(o.quantity_product * p.price), 0)
FROM orders o JOIN customers c ON o.customer_id = c.customer_id JOIN product p ON o.product_id = p.product_id
WHERE (strftime('%Y', o.date) - strftime('%Y', c.birth_date)) = 24
  AND (strftime('%m', o.date) || strftime('%d', o.date)) < (strftime('%m', c.birth_date) || strftime('%d', c.birth_date))"""


def age_at(birth, d):
    return d.year - birth.year - ((d.month, d.day) < (birth.month, birth.day))


def c10(db, by_case, ref):
    print("\n=== C10 evidence on", db, "===")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cells = by_case["C10"]
    for (p, m), r in sorted(cells.items()):
        got = con.execute(r["sql"]).fetchone()[0]
        print(f"   replay {short(p, m):28s} trace={r['value']:>7}  rerun={got:>7}  ({r['verdict']})")
    ref_v = con.execute(REF_C10).fetchone()[0]
    wrong_v = con.execute(f"SELECT COALESCE(SUM(o.quantity_product*p.price),0) FROM orders o "
                          f"JOIN product p ON p.product_id=o.product_id JOIN customers c ON c.customer_id=o.customer_id "
                          f"WHERE {FAULTY_WHERE}").fetchone()[0]
    print(f"   reference query = {ref_v} (reference-td1.csv: {ref['C10']})  | shared faulty condition = {wrong_v}")
    print(f"   Qwen 2nd branch (age 23): lines, revenue = {con.execute(QWEN_BRANCH2).fetchone()}")

    missed = con.execute(DELTA_MISSED).fetchall()
    added = con.execute(DELTA_ADDED).fetchall()
    print(f"\n   Delta - MISSED by the faulty queries: {len(missed)} customers")
    print("   customer_id | birth_date | lines | first_order | last_order | revenue_cents_ht")
    for row in missed:
        print("   " + " | ".join(str(x) for x in row))
    s = sum(r[-1] for r in missed)
    print(f"   sum missed = {s} ; wrongly added = {sum(r[-1] for r in added)} ({len(added)} customers)")
    print(f"   reference - wrong = {ref_v - wrong_v} -> {'EXACT' if s - sum(r[-1] for r in added) == ref_v - wrong_v else 'MISMATCH'}")

    # Independent check: Python computes the completed age at each order date
    tot = py_missed = 0
    q = ("SELECT c.birth_date, o.date, o.quantity_product*p.price FROM orders o "
         "JOIN product p ON p.product_id=o.product_id JOIN customers c ON c.customer_id=o.customer_id")
    for bd, od, amount in con.execute(q):
        b, d = date.fromisoformat(bd[:10]), date.fromisoformat(od[:10])
        if age_at(b, d) == 25:
            tot += amount
            if d.year - b.year == 26:          # birthday not yet passed in the order year
                py_missed += amount
    print(f"\n   Independent Python check: age-25 revenue = {tot} ; of which year-diff-26 = {py_missed}")
    con.close()


def demo_vote():
    print("\n=== DEMO-VOTE (constructed teaching example, not model output) ===")
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE sales(sale_date TEXT, amount_cents INTEGER)")
    con.execute("INSERT INTO sales VALUES ('2026-01-01', 100)")
    gt = con.execute("SELECT COALESCE(SUM(amount_cents),0) FROM sales WHERE sale_date >  '2026-01-01' AND sale_date < '2026-01-02'").fetchone()[0]
    ge = con.execute("SELECT COALESCE(SUM(amount_cents),0) FROM sales WHERE sale_date >= '2026-01-01' AND sale_date < '2026-01-02'").fetchone()[0]
    r = vote([("P1", gt), ("P2", gt), ("P3", ge)], 2)
    print(f"   '>' -> {gt} ; '>=' -> {ge} ; reference 100 ; 2-of-3 on [{gt}, {gt}, {ge}] -> {r['value']} ({r['votes']} votes)")


HERE = Path(__file__).resolve().parent          # td2/B/scripts
ROOT = HERE.parents[2]                           # repository root
PAIR_A = HERE.parents[1] / "A" / "scripts"       # pair A's completed skeleton


def pair_a_check(by_case, cases):
    """Recompute 2-of-3 and 3-of-5 with pair A's vote_k_sur_n and compare with ours."""
    print("\n=== Cross-check with pair A's vote_k_sur_n ===")
    sys.path.insert(0, str(PAIR_A))
    spec = importlib.util.spec_from_file_location("skeleton_pair_a", PAIR_A / "skeleton-multi-llm-en.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    vote_a = lambda props, k: mod.Orchestrateur.vote_k_sur_n(None, props, k)
    diffs = 0
    for q in cases:
        cells = by_case[q]
        def ns(pm):
            v = as_vote(cells.get(pm))
            return SimpleNamespace(provider=pm[0], model_requested=pm[1], value=v,
                                   verdict="executed" if v is not None else "error")
        for label, pms, k in (("2-of-3", PANEL_3, 2), ("3-of-5", sorted(cells), 3)):
            a = vote_a([ns(pm) for pm in pms], k)
            ours = vote([(f"{p}:{m}", as_vote(cells.get((p, m)))) for p, m in pms], k)
            same = (a["consensus"], a["value"], a["votes"]) == (ours["consensus"], ours["value"], ours["votes"])
            diffs += not same
            print(f"   {q} {label}: pair A = {a['value'] if a['consensus'] else 'ABSTAIN'} ({a['votes']} votes) "
                  f"| ours = {ours['value'] if ours['consensus'] else 'ABSTAIN'} ({ours['votes']} votes) "
                  f"-> {'same' if same else 'DIFFERENT'}")
    print(f"   differences: {diffs}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", default=str(ROOT / "td1/data/traces/traces-td1.csv"))
    ap.add_argument("--reference", default=str(ROOT / "td1/data/references/reference-td1.csv"))
    ap.add_argument("--db", required=True, help="<student-kit-dir>/data/boutique.sqlite")
    a = ap.parse_args()
    with open(a.reference, encoding="utf-8", newline="") as f:
        ref = {r["case_id"]: int(r["revenue_cents"]) for r in csv.DictReader(f)}
    by_case = scan(last_attempts(a.traces), ref)
    c10(a.db, by_case, ref)
    demo_vote()
    pair_a_check(by_case, ["C02", "C08", "C10", "C15"])


if __name__ == "__main__":
    main()
