#!/usr/bin/env python3
"""TD 2, step 3 (pair C): derive the TD 1 accuracy rate of every question family,
and cross-check what a 2-of-3 panel and a 3-of-5 quorum would have returned.

No network, no key, no model call. The only inputs are the files committed in
TD 1:

    td1/analysis/csv/model-question-comparison-en.csv   one final row per model/question
    td1/data/references/reference-td1.csv               our independent reference values

Outputs (regenerated, never hand-typed):

    td2/analysis/csv/family-rates-td1.csv       correct / cases and failing cells, per family and model
    td2/analysis/csv/quorum-by-family-td1.csv   per question: 2-of-3 and 3-of-5 outcome vs the reference

The vote implemented here follows the same contract as
`Orchestrateur.vote_k_sur_n` in `skeleton-multi-llm-en.py` (pair A). It is
written independently so that the two pairs can compare results: a cell with no
value (`sql_invalid`, `sql_rejected`, `not_executed`) stays in n and casts no
vote, k must be a strict majority, and a duplicate (provider, model) is refused.

    python3 td2/scripts/family_rates_td2.py            # write the two CSV files
    python3 td2/scripts/family_rates_td2.py --print    # also print the tables
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

TD2 = Path(__file__).resolve().parents[1]
ROOT = TD2.parent
TD1 = ROOT / "td1"
COMPARISON = TD1 / "analysis" / "csv" / "model-question-comparison-en.csv"
REFERENCE = TD1 / "data" / "references" / "reference-td1.csv"
OUT_RATES = TD2 / "analysis" / "csv" / "family-rates-td1.csv"
OUT_QUORUM = TD2 / "analysis" / "csv" / "quorum-by-family-td1.csv"

# Families as defined by the question types of questions-td1-en.md.
FAMILIES = [
    ("F1", "period", ["C01", "C04", "C05", "C06", "C07", "C20"]),
    ("F2", "completed age on a reference date", ["C02", "C08", "C09", "C11"]),
    ("F2b", "age at the time of the order", ["C10"]),
    ("F3", "product list", ["C03", "C12", "C13", "C14"]),
    ("F4", "combined filters", ["C15", "C16", "C17", "C18", "C19"]),
]

# The five models of TD 1, in the order of modeles-autorises.json.
MODELS = [
    "groq:openai/gpt-oss-120b",
    "groq:openai/gpt-oss-20b",
    "openrouter:cohere/north-mini-code:free",
    "groq:qwen/qwen3.8-27b",
    "openrouter:dots-studio/dots-3-note-preview:free",
]

# The fixed panel of atelier-vote.py: three distinct families, threshold k = 2.
PANEL_2OF3 = [
    "groq:openai/gpt-oss-120b",
    "openrouter:cohere/north-mini-code:free",
    "groq:qwen/qwen3.8-27b",
]

# The panels our own routing rule declares, per family: only models that TD 1
# shows correct on the family, three distinct model families, two providers.
# F2b has no entry on purpose: C10 shows every admissible panel fails there.
RULE_PANELS = {
    "F1": (["groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b",
            "openrouter:dots-studio/dots-3-note-preview:free"], 2),
    "F2": (["groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b",
            "openrouter:dots-studio/dots-3-note-preview:free"], 2),
    "F3": (["groq:openai/gpt-oss-120b", "openrouter:cohere/north-mini-code:free",
            "openrouter:dots-studio/dots-3-note-preview:free"], 2),
    "F4": (MODELS, 3),
}

CASES = [f"C{i:02d}" for i in range(1, 21)]


def vote_k_of_n(proposals: list[dict], k: int) -> dict:
    """Same contract as `vote_k_sur_n`: keep a value or abstain, never invent one.

    `proposals` is the panel for one question; each item carries `model`
    ("provider:model_requested"), `value` (int cents or None) and `verdict`.
    """
    n = len(proposals)
    seen = Counter(p["model"] for p in proposals)
    duplicates = [m for m, c in seen.items() if c > 1]
    if duplicates:
        raise ValueError(f"duplicate panel member, not a second vote: {duplicates}")
    if not n // 2 < k <= n:
        raise ValueError(f"k = {k} is not a strict majority of n = {n}")
    ballots = [p["value"] for p in proposals
               if p["verdict"] == "executed" and p["value"] is not None]
    tally = Counter(ballots)
    if not tally:
        return {"consensus": False, "value": None, "votes": 0, "models": []}
    value, votes = tally.most_common(1)[0]
    if votes >= k:
        models = [p["model"] for p in proposals
                  if p["verdict"] == "executed" and p["value"] == value]
        return {"consensus": True, "value": value, "votes": votes, "models": models}
    return {"consensus": False, "value": None, "votes": votes, "models": []}


def load_cells() -> dict[tuple[str, str], dict]:
    """One final cell per (case, model), read from the TD 1 comparison table."""
    cells: dict[tuple[str, str], dict] = {}
    with COMPARISON.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            raw = (row["value_cents"] or "").strip()
            # A cell with no value (sql_invalid, sql_rejected, not_executed)
            # stays in n and casts no vote: `executed` means a value came back.
            value = int(raw) if raw else None
            cells[(row["case_id"], row["model_id"])] = {
                "model": row["model_id"],
                "status": row["status"],
                "value": value,
                "verdict": "executed" if value is not None else "error",
                "nature": row["nature"],
            }
    return cells


def load_reference() -> dict[str, int]:
    with REFERENCE.open(encoding="utf-8-sig", newline="") as handle:
        return {row["case_id"]: int(row["revenue_cents"]) for row in csv.DictReader(handle)}


def family_of(case: str) -> tuple[str, str]:
    for key, label, cases in FAMILIES:
        if case in cases:
            return key, label
    raise KeyError(case)


def build_rates(cells, reference):
    """correct / cases per family and model, with the failing cells named."""
    rows = []
    for key, label, cases in FAMILIES:
        for model in MODELS:
            correct, failing = 0, []
            for case in cases:
                cell = cells[(case, model)]
                if cell["status"] == "correct":
                    correct += 1
                else:
                    got = "" if cell["value"] is None else f"={cell['value']}"
                    failing.append(f"{case} ({cell['status']}{got}, "
                                   f"reference {reference[case]})")
            rows.append({
                "family": key,
                "family_label": label,
                "cases": " ".join(cases),
                "model_id": model,
                "correct": correct,
                "total": len(cases),
                "rate_percent": round(100 * correct / len(cases), 1),
                "failing_cells": "; ".join(failing) or "none",
            })
        # Panel line: the five models pooled on the family.
        pooled_correct = sum(1 for case in cases for model in MODELS
                             if cells[(case, model)]["status"] == "correct")
        pooled_total = len(cases) * len(MODELS)
        rows.append({
            "family": key,
            "family_label": label,
            "cases": " ".join(cases),
            "model_id": "ALL FIVE (pooled cells)",
            "correct": pooled_correct,
            "total": pooled_total,
            "rate_percent": round(100 * pooled_correct / pooled_total, 1),
            "failing_cells": "",
        })
    return rows


def build_quorum(cells, reference):
    """What the fixed 2-of-3 panel and the 3-of-5 quorum return, per question."""
    rows = []
    for case in CASES:
        key, label = family_of(case)
        panel = [dict(cells[(case, m)]) for m in PANEL_2OF3]
        quorum = [dict(cells[(case, m)]) for m in MODELS]
        d2 = vote_k_of_n(panel, 2)
        d3 = vote_k_of_n(quorum, 3)
        ref = reference[case]
        rule_members, rule_k = RULE_PANELS.get(key, (None, None))
        if rule_members is None:
            dr = {"consensus": False, "value": None, "votes": 0, "models": []}
            rule_label = "no panel admissible (see C10)"
        else:
            dr = vote_k_of_n([dict(cells[(case, m)]) for m in rule_members], rule_k)
            rule_label = f"{rule_k}-of-{len(rule_members)}"
        rows.append({
            "case_id": case,
            "family": key,
            "reference_cents": ref,
            "panel_2of3_decision": "consensus" if d2["consensus"] else "abstention",
            "panel_2of3_value": "" if d2["value"] is None else d2["value"],
            "panel_2of3_votes": d2["votes"],
            "panel_2of3_agrees": "" if not d2["consensus"] else ("yes" if d2["value"] == ref else "NO"),
            "quorum_3of5_decision": "consensus" if d3["consensus"] else "abstention",
            "quorum_3of5_value": "" if d3["value"] is None else d3["value"],
            "quorum_3of5_votes": d3["votes"],
            "quorum_3of5_agrees": "" if not d3["consensus"] else ("yes" if d3["value"] == ref else "NO"),
            "quorum_3of5_models": " ".join(d3["models"]),
            "rule_panel": rule_label,
            "rule_panel_decision": "consensus" if dr["consensus"] else "abstention",
            "rule_panel_value": "" if dr["value"] is None else dr["value"],
            "rule_panel_votes": dr["votes"],
            "rule_panel_agrees": "" if not dr["consensus"] else ("yes" if dr["value"] == ref else "NO"),
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarise(quorum_rows) -> None:
    """Per family: how often each configuration returns the reference."""
    print("\nreference / wrong / abstention, per family")
    print(f"{'family':6s} {'cases':6s} {'fixed 2-of-3':>14s} {'3-of-5':>14s} {'our rule panel':>14s}")
    for key, label, cases in FAMILIES:
        rows = [r for r in quorum_rows if r["family"] == key]
        def counts(prefix):
            ok = sum(1 for r in rows if r[f"{prefix}_agrees"] == "yes")
            bad = sum(1 for r in rows if r[f"{prefix}_agrees"] == "NO")
            abst = sum(1 for r in rows if r[f"{prefix}_decision"] == "abstention")
            return f"{ok} / {bad} / {abst}"
        print(f"{key:6s} {len(cases):<6d} {counts('panel_2of3'):>14s} "
              f"{counts('quorum_3of5'):>14s} {counts('rule_panel'):>14s}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print", action="store_true", dest="show",
                        help="print the tables as well as writing the CSV files")
    args = parser.parse_args()

    cells = load_cells()
    reference = load_reference()
    missing = [(c, m) for c in CASES for m in MODELS if (c, m) not in cells]
    if missing:
        raise SystemExit(f"incomplete comparison table, missing cells: {missing}")

    rates = build_rates(cells, reference)
    quorum = build_quorum(cells, reference)
    write_csv(OUT_RATES, rates)
    write_csv(OUT_QUORUM, quorum)
    print(f"wrote {OUT_RATES.relative_to(ROOT)} ({len(rates)} rows)")
    print(f"wrote {OUT_QUORUM.relative_to(ROOT)} ({len(quorum)} rows)")

    if args.show:
        print("\n--- correct / cases per family and model (TD 1, 100 real cells) ---")
        for row in rates:
            print(f"{row['family']:4s} {row['model_id']:48s} "
                  f"{row['correct']}/{row['total']:<3d} {row['rate_percent']:5.1f}%  "
                  f"{row['failing_cells']}")
        print("\n--- what the quorum would have returned ---")
        for row in quorum:
            print(f"{row['case_id']} {row['family']:4s} ref={row['reference_cents']:<9d} "
                  f"2of3={row['panel_2of3_decision']:<11s} {str(row['panel_2of3_value']):<9s} "
                  f"v={row['panel_2of3_votes']} {row['panel_2of3_agrees']:<3s} | "
                  f"3of5={row['quorum_3of5_decision']:<11s} {str(row['quorum_3of5_value']):<9s} "
                  f"v={row['quorum_3of5_votes']} {row['quorum_3of5_agrees']:<3s} | "
                  f"rule({row['rule_panel']})={row['rule_panel_decision']:<11s} "
                  f"{str(row['rule_panel_value']):<9s} v={row['rule_panel_votes']} "
                  f"{row['rule_panel_agrees']}")
        summarise(quorum)


if __name__ == "__main__":
    main()
