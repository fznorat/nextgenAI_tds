#!/usr/bin/env python3
"""TD 2, step 3 (pair C): the kit's routing simulator, adapted to our rule.

Adapted from `td2/C/scripts/atelier-routage.py` (kit pack 2026-10-18, unchanged copy
kept next to this file so the "before" output can be reproduced). What changed:

  * `RESOURCES` holds our five TD 1 models with their *measured* per-family
    results and the routes of the portfolio, instead of three fictitious ones.
    Eligibility is per family, not one `level` number: TD 1 shows a model can be
    4/4 on one family and 2/4 on another (gpt-oss-20b: F4 5/5 but F2 2/4), so a
    single capability scalar cannot carry the rule.
  * `choose` applies our rule: the check comes from the question family *and*
    from the cost of an error for the use, it tightens when the model that
    answers is not 100 % on the family in TD 1, and it is deterministic (never a
    vote) on the family where our own traces show the quorum returning a wrong
    value (C10).
  * every decision carries the TD 1 cells that justify it in `reason`, the
    number of model calls the check costs, and the API-equivalent price of those
    calls (N/A with its coverage when a model has no documented billed route).
  * the kit's seven scenarios still run (difficulty/high_impact are mapped onto
    family/use), so the before/after outputs compare line by line.

No API call, no key, no network. Availability is supplied by a scenario, never
measured from a provider. Prices are per request, USD excluding tax, computed on
one fixed token envelope (TD 1 medians); they are a computation under written
assumptions, not a measured bill.

    python3 td2/C/scripts/atelier-routage-td2.py                        # every scenario
    python3 td2/C/scripts/atelier-routage-td2.py --scenario deferrable  # one scenario
    python3 td2/C/scripts/atelier-routage-td2.py --table                # readable table
    python3 td2/C/scripts/atelier-routage-td2.py --rule                 # the rule itself
    python3 td2/C/scripts/atelier-routage-td2.py --check-rates          # TD 1 numbers vs the CSV
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PAIR_C = Path(__file__).resolve().parents[1]
RATES_CSV = PAIR_C / "analysis" / "csv" / "family-rates-td1.csv"

# --------------------------------------------------------------------------
# Cost basis. Written assumptions, all dated, all from the kit.
# --------------------------------------------------------------------------
# Envelope: medians of the 100 executed TD 1 cells (traces-td1.csv, http 200).
ENVELOPE = {"input_tokens": 626, "output_tokens": 140}
# Groq counts reasoning inside tokens_completion (checked on the 40 TD 1 rows
# that carry a reasoning counter: completion >= reasoning on every row), so
# reasoning tokens are information only and are not added. methode-cout, step 1.
# Prices: Groq Developer catalogue of 5 October 2026 (methode-cout, step 2) and
# the portfolio snapshot of 28 September 2026 (portefeuille-modeles-2026-09-28).
USD_PER_EUR = 1.1403  # implied by the portfolio's own paired columns: 0.15 USD -> 0.1315 EUR


def per_request_usd(input_usd_per_m: float, output_usd_per_m: float) -> float:
    """API-equivalent price of one request on the envelope above, USD excl. tax."""
    return round((ENVELOPE["input_tokens"] * input_usd_per_m
                  + ENVELOPE["output_tokens"] * output_usd_per_m) / 1_000_000, 8)


def per_request_usd_from_eur(input_eur_per_m: float, output_eur_per_m: float) -> float:
    """Same, from the portfolio's effective subscription columns (EUR per million)."""
    eur = (ENVELOPE["input_tokens"] * input_eur_per_m
           + ENVELOPE["output_tokens"] * output_eur_per_m) / 1_000_000
    return round(eur * USD_PER_EUR, 8)


def td1(correct: int, cases: int, cells: str) -> dict:
    return {"correct": correct, "cases": cases, "cells": cells}


# --------------------------------------------------------------------------
# Resources: our five TD 1 models and the escalation routes of the portfolio.
#
#   access       free | subscription | paid, as the portfolio's `acces` column
#   cash         new money spent at request time (0 on a free or included route)
#   allocation   share of an already paid envelope consumed by the call
#   api_equivalent_usd   price of this call on a *documented billed route of the
#                exact same model*; None means N/A, which is not zero
#   td1          measured results per family; None means never measured
# --------------------------------------------------------------------------
RESOURCES = [
    {"id": "groq:openai/gpt-oss-120b", "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None,
     "api_equivalent_usd": per_request_usd(0.15, 0.60),
     "retries_td1": 0, "latency_ms_median": 841,
     "limit_td1": "Groq Free plan, member A's account; no HTTP 429 in TD 1",
     "td1": {"F1": td1(6, 6, "C01,C04,C05,C06,C07,C20"),
             "F2": td1(4, 4, "C02,C08,C09,C11"),
             "F2b": td1(1, 1, "C10"),
             "F3": td1(4, 4, "C03,C12,C13,C14"),
             "F4": td1(4, 5, "C15,C16,C17,C18 correct; C19 wrong 0 vs 1990")}},

    {"id": "groq:openai/gpt-oss-20b", "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None,
     "api_equivalent_usd": per_request_usd(0.075, 0.30),
     "retries_td1": 1, "latency_ms_median": 684,
     "limit_td1": "Groq Free plan; 1 HTTP 429 in TD 1 (TPM 8000, C19), 1 retry",
     "td1": {"F1": td1(6, 6, "C01,C04,C05,C06,C07,C20"),
             "F2": td1(2, 4, "C08,C09 correct; C02 wrong 0, C11 wrong 322160"),
             "F2b": td1(1, 1, "C10"),
             "F3": td1(4, 4, "C03,C12,C13,C14"),
             "F4": td1(5, 5, "C15,C16,C17,C18,C19")}},

    {"id": "openrouter:cohere/north-mini-code:free", "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None,
     "api_equivalent_usd": None,  # N/A: no documented paid route of the exact same model
     "retries_td1": 0, "latency_ms_median": 2415,
     "limit_td1": "OpenRouter :free route, member C's account; no 429 in TD 1",
     "td1": {"F1": td1(6, 6, "C01,C04,C05,C06,C07,C20"),
             "F2": td1(0, 4, "C02 sql_invalid; C08,C09,C11 wrong 0"),
             "F2b": td1(0, 1, "C10 wrong 119410 vs 558980"),
             "F3": td1(4, 4, "C03,C12,C13,C14"),
             "F4": td1(3, 5, "C16,C18,C19 correct; C15 wrong 0, C17 wrong 197080")}},

    {"id": "groq:qwen/qwen3.8-27b", "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None,
     "api_equivalent_usd": per_request_usd(0.80, 4.00),
     "retries_td1": 5, "latency_ms_median": 418,
     "limit_td1": "Groq Free plan; 5 HTTP 429 in TD 1 (OTPM 1000, C16-C20), 5 retries",
     "td1": {"F1": td1(6, 6, "C01,C04,C05,C06,C07,C20"),
             "F2": td1(4, 4, "C02,C08,C09,C11"),
             "F2b": td1(0, 1, "C10 wrong 119410 vs 558980"),
             "F3": td1(3, 4, "C03,C13,C14 correct; C12 sql_rejected (unclosed fence)"),
             "F4": td1(2, 5, "C16,C18 correct; C15 wrong 0, C17 wrong 248490, C19 wrong 83580")}},

    {"id": "openrouter:dots-studio/dots-3-note-preview:free", "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None,
     "api_equivalent_usd": None,  # N/A: no documented paid route of the exact same model
     "retries_td1": 0, "latency_ms_median": 2762,
     "limit_td1": "OpenRouter :free route, member E's account; no 429 in TD 1",
     "td1": {"F1": td1(6, 6, "C01,C04,C05,C06,C07,C20"),
             "F2": td1(2, 4, "C09,C11 correct; C02 wrong 0, C08 wrong 0"),
             "F2b": td1(0, 1, "C10 wrong 119410 vs 558980"),
             "F3": td1(4, 4, "C03,C12,C13,C14"),
             "F4": td1(3, 5, "C16,C18,C19 correct; C15 wrong 138920, C17 sql_invalid")}},

    # Escalation 1: a documented billed route of the *exact same model* as our
    # best measured one, so the TD 1 cells transfer (methode-cout, step 2: a
    # shared family name does not establish model identity).
    {"id": "groq-developer:openai/gpt-oss-120b", "access": "paid", "available": True,
     "cash": per_request_usd(0.15, 0.60), "allocation": per_request_usd(0.15, 0.60),
     "reset_minutes": None, "api_equivalent_usd": per_request_usd(0.15, 0.60),
     "rates_from": "groq:openai/gpt-oss-120b",
     "retries_td1": 0, "latency_ms_median": 841,
     "limit_td1": "billed route, no free-plan per-minute cap; prices of 5 Oct 2026",
     "td1": {"F1": td1(6, 6, "C01,C04,C05,C06,C07,C20"),
             "F2": td1(4, 4, "C02,C08,C09,C11"),
             "F2b": td1(1, 1, "C10"),
             "F3": td1(4, 4, "C03,C12,C13,C14"),
             "F4": td1(4, 5, "C15,C16,C17,C18 correct; C19 wrong 0 vs 1990")}},

    # Escalation 2: included capacity of a subscription we already pay for
    # (portfolio G3, `codex`, `retenu`). Never measured on the twenty questions,
    # so the rule only allows it behind the deterministic reference check.
    {"id": "codex:gpt-5.6-luna", "access": "subscription", "available": True,
     "cash": 0.0, "allocation": per_request_usd_from_eur(0.0126, 0.0758),
     "allocation_remaining": 0.02, "reserve_high_impact": 0.015,
     "reset_minutes": None, "api_equivalent_usd": per_request_usd(0.2, 1.2),
     "retries_td1": 0, "latency_ms_median": None,
     "limit_td1": "subscription included capacity; monthly envelope, not a per-minute cap",
     "td1": None},
]

# --------------------------------------------------------------------------
# The rule. One entry per question family of questions-td1-en.md.
#
# `check` is the floor for each use; it is tightened by `tighten_for_model`
# when the model that answers is not 100 % on the family in TD 1.
# Order of strictness: none < quorum_2of3 < quorum_3of5 < reference.
# --------------------------------------------------------------------------
CHECK_ORDER = ["none", "quorum_2of3", "quorum_3of5", "reference"]

RULE = {
    "F1": {
        "label": "period",
        "cases": "C01,C04,C05,C06,C07,C20",
        "pooled": "30/30 cells correct (five models)",
        "panel": ["groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b",
                  "openrouter:dots-studio/dots-3-note-preview:free"],
        "check": {"internal_dashboard": "none",
                  "customer_facing": "quorum_2of3",
                  "payout": "reference"},
        "note": "`none` is admissible here: the model called is 6/6 on the family "
                "and the use is a low-stakes internal dashboard.",
    },
    "F2": {
        "label": "completed age on a reference date",
        "cases": "C02,C08,C09,C11",
        "pooled": "12/20 cells correct (five models)",
        "panel": ["groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b",
                  "openrouter:dots-studio/dots-3-note-preview:free"],
        "check": {"internal_dashboard": "none",
                  "customer_facing": "quorum_2of3",
                  "payout": "reference"},
        "note": "`none` only with gpt-oss-120b or qwen3.8-27b (4/4). Any other model "
                "erred on C02, C08, C09 or C11 and is checked.",
    },
    "F2b": {
        "label": "age at the time of the order",
        "cases": "C10",
        "pooled": "2/5 cells correct (five models)",
        "panel": None,  # proven inadmissible, see `check`
        "check": {"internal_dashboard": "reference",
                  "customer_facing": "reference",
                  "payout": "reference"},
        "note": "No vote on this family at any stake. On C10 cohere, qwen and dots all "
                "return 119410 instead of 558980: the fixed 2-of-3 panel returns 119410 "
                "(2 votes of 3) and the 3-of-5 quorum returns 119410 (3 votes of 5). The "
                "only 2-of-3 panel that returns the reference is gpt-oss-120b + "
                "gpt-oss-20b + any third, i.e. two members of the same model family, "
                "which is what lecture 2 tells us not to buy safety with.",
    },
    "F3": {
        "label": "product list",
        "cases": "C03,C12,C13,C14",
        "pooled": "19/20 cells correct (five models)",
        "panel": ["groq:openai/gpt-oss-120b", "openrouter:cohere/north-mini-code:free",
                  "openrouter:dots-studio/dots-3-note-preview:free"],
        "check": {"internal_dashboard": "none",
                  "customer_facing": "quorum_2of3",
                  "payout": "reference"},
        "note": "qwen3.8-27b is excluded as first call: C12 was rejected for an unclosed "
                "```sql fence (format, not logic), and a rejected cell is still a lost cell.",
    },
    "F4": {
        "label": "combined filters (period, age, product)",
        "cases": "C15,C16,C17,C18,C19",
        "pooled": "17/25 cells correct (five models)",
        "panel": [r["id"] for r in RESOURCES if r["access"] == "free"],
        "check": {"internal_dashboard": "quorum_3of5",
                  "customer_facing": "quorum_3of5",
                  "payout": "reference"},
        "note": "`none` with gpt-oss-20b (5/5 on C15-C19) would be admissible by the letter "
                "of the constraint; we refuse it. Four of five models erred on this family, "
                "the fixed 2-of-3 panel returned a wrong value on C15 (0 instead of 168680), "
                "and the five routes are free: the quorum costs quota and latency, not money.",
    },
}

USES = {
    "internal_dashboard": "internal dashboard, low stakes",
    "customer_facing": "figure shown to the customer",
    "payout": "amount paid out",
}

CHECK_TEXT = {
    "none": "read-only execution and value plausibility check",
    "quorum_2of3": "2-of-3 quorum on the family panel, abstain if no value reaches k",
    "quorum_3of5": "3-of-5 quorum on the five TD 1 families, abstain if no value reaches k",
    "reference": "deterministic check against the parameterised reference query on the "
                 "read-only database, abstain and escalate to review on disagreement",
}

# The reference check of a payout is paired with a human review.
REVIEW_USES = {"payout"}

# Deferring is only admissible when the wake-up leaves room to re-measure
# availability and to pay for one retry inside the deadline.
WAKE_MARGIN_MINUTES = 5

# Mapping used so the kit's seven scenarios still run against this rule.
DIFFICULTY_TO_FAMILY = {1: "F1", 2: "F2", 3: "F4"}


# --------------------------------------------------------------------------
# The policy.
# --------------------------------------------------------------------------
def is_perfect(resource: dict, family: str) -> bool:
    """TD 1 shows this model correct on every cell of the family."""
    measured = (resource["td1"] or {}).get(family)
    return bool(measured) and measured["correct"] == measured["cases"]


def td1_quote(resource: dict, family: str) -> str:
    measured = (resource["td1"] or {}).get(family)
    if not measured:
        return "no TD 1 measurement for this model on this family"
    return (f"TD 1 {measured['correct']}/{measured['cases']} on {family} "
            f"({measured['cells']})")


def stricter(a: str, b: str) -> str:
    return a if CHECK_ORDER.index(a) >= CHECK_ORDER.index(b) else b


def tighten_for_model(check: str, resource: dict, family: str) -> str:
    """A model that erred on the family in TD 1 never answers unchecked."""
    if is_perfect(resource, family):
        return check
    if (resource["td1"] or {}).get(family) is None:
        # Never measured: only the deterministic check makes it admissible.
        return "reference"
    return stricter(check, "quorum_2of3")


def preference_order(resources: list[dict], family: str) -> list[dict]:
    """Cheapest first among the models TD 1 shows correct on the family.

    At request time every free route costs 0, so the tie is broken by the price
    the portfolio does document for the exact same model (what the same
    configuration would cost a company), then by the rate-limit friction
    measured in TD 1, then by latency. A route whose billed equivalent is N/A
    cannot be called the cheapest, so it is ordered last among equals.
    """
    return sorted(resources, key=lambda r: (
        0 if is_perfect(r, family) else 1,
        r["cash"],          # nothing new spent at request time comes first
        r["allocation"],    # then the smallest share of an envelope already paid
        r["api_equivalent_usd"] if r["api_equivalent_usd"] is not None else float("inf"),
        r["retries_td1"],
        r["latency_ms_median"] if r["latency_ms_median"] is not None else 10 ** 6,
        r["id"],
    ))


def price_calls(members: list[dict]) -> dict:
    """API equivalent of a set of calls, or N/A with its coverage.

    methode-cout, step 4: a quorum counts every model consulted, and a partly
    quantifiable configuration is marked N/A with its coverage, never projected.
    """
    known = [r for r in members if r["api_equivalent_usd"] is not None]
    missing = [r["id"] for r in members if r["api_equivalent_usd"] is None]
    subtotal = round(sum(r["api_equivalent_usd"] for r in known), 8)
    if missing:
        return {"value": "N/A", "known_subtotal_usd": subtotal,
                "coverage": f"{len(known)}/{len(members)} calls priced",
                "missing_route": missing}
    return {"value": subtotal, "coverage": f"{len(members)}/{len(members)} calls priced"}


def decision(action, req, check, reason, resource=None, calls=None, **extra) -> dict:
    calls = calls if calls is not None else ([resource] if resource else [])
    checks = CHECK_TEXT[check]
    if req["use"] in REVIEW_USES:
        checks += "; human review before the amount is paid"
    out = {
        "action": action,
        "resource": resource["id"] if resource else None,
        "calls": [r["id"] for r in calls],
        "cash": round(sum(r["cash"] for r in calls), 8),
        "allocation": round(sum(r["allocation"] for r in calls), 8),
        "api_equivalent_usd": price_calls(calls) if calls else None,
        "check": check,
        "checks": checks,
        "reason": reason,
    }
    out.update(extra)
    return out


def choose(request: dict, resources: list[dict]) -> dict:
    """Our rule, with a reason that cites the TD 1 cells behind every decision.

    Branch order, and why: already paid capacity before new spending (a free
    route, then included subscription capacity), a nonurgent request may wait
    for a free route to refill, new money last, abstention rather than an
    unchecked value. The one reversal of the kit's order is marked
    `defer_before_included` and is explained in td2/C/README.md.
    """
    req = normalise(request)
    family, use = req["family"], req["use"]
    plan = RULE.get(family)
    if plan is None:
        # The kit's "unknown capability" case: nothing in TD 1 measures it.
        return decision("abstain", req, "reference",
                        f"family {family!r} is not in the rule: the twenty TD 1 questions "
                        f"measure no cell for it, and the rule does not route a question "
                        f"whose family has no measured rate")

    floor = plan["check"][use]

    # 1. Who may answer. The deterministic check settles the value itself, so it
    #    is the only check that makes an unmeasured model admissible.
    if floor == "reference":
        admissible = [r for r in resources if r["td1"] is not None or r["access"] != "free"]
    else:
        admissible = [r for r in resources if is_perfect(r, family)]
    if not admissible:
        return decision("abstain", req, floor,
                        f"{family} {plan['label']}: no model is 100 % on {plan['cases']} in "
                        f"TD 1 ({plan['pooled']}), and the rule refuses to answer a "
                        f"{USES[use]} with a model that erred on the family")

    ordered = preference_order(admissible, family)
    free_available = [r for r in ordered if r["available"] and r["cash"] == 0 and r["allocation"] == 0]
    included_sub = [r for r in ordered if r["available"] and r["cash"] == 0 and r["allocation"] > 0]
    waiting_free = [r for r in ordered
                    if not r["available"] and r["cash"] == 0 and r["allocation"] == 0
                    and r["reset_minutes"] is not None
                    and 0 < r["reset_minutes"] + WAKE_MARGIN_MINUTES <= req["deadline_minutes"]]
    paid = [r for r in ordered if r["available"] and r["cash"] > 0 and r["cash"] <= req["budget"]]

    # 2. A quorum needs enough available members of the declared panel.
    if floor in ("quorum_2of3", "quorum_3of5"):
        k = 2 if floor == "quorum_2of3" else 3
        panel = [r for r in resources if r["id"] in (plan["panel"] or [])]
        present = preference_order([r for r in panel if r["available"]], family)
        if len(present) < k:
            # An unavailable member stays in n but casts no vote: with fewer than
            # k possible votes the quorum cannot conclude, so the rule falls back
            # on the deterministic check rather than on a thinner vote.
            floor = "reference"
            admissible = [r for r in resources if r["td1"] is not None or r["access"] != "free"]
            ordered = preference_order(admissible, family)
            free_available = [r for r in ordered if r["available"] and r["cash"] == 0 and r["allocation"] == 0]
            included_sub = [r for r in ordered if r["available"] and r["cash"] == 0 and r["allocation"] > 0]
            paid = [r for r in ordered if r["available"] and r["cash"] > 0 and r["cash"] <= req["budget"]]
            quorum_note = (f"panel incomplete ({len(present)} of {len(panel)} members available, "
                           f"k = {k}): a vote that cannot reach k is replaced by the "
                           f"deterministic check, not by a thinner vote")
        else:
            chosen = present[0]
            cells = "; ".join(td1_quote(r, family) for r in present)
            return decision(
                "run", req, floor, resource=chosen, calls=present,
                votes_required=k, panel_size=len(panel),
                panel_available=[r["id"] for r in present],
                reason=(f"{family} {plan['label']}, {USES[use]}: {floor} on the family panel. "
                        f"{plan['pooled']}; members called: {cells}. "
                        f"Unavailable members stay in n and cast no vote. {plan['note']}"))
    else:
        quorum_note = ""

    # 3. Single-model branches, in order of what has already been paid for.
    if free_available:
        chosen = free_available[0]
        check = tighten_for_model(floor, chosen, family)
        reason = (f"{family} {plan['label']}, {USES[use]}: {chosen['id']} is the cheapest "
                  f"eligible free route ({td1_quote(chosen, family)}). "
                  f"Check {check}. {quorum_note or plan['note']}").strip()
        if check != floor:
            reason += f" Check tightened from {floor} to {check} for this model."
        return decision("run", req, check, resource=chosen, reason=reason,
                        next_if_unavailable=[r["id"] for r in free_available[1:]] or None)

    # 3b. Included subscription capacity is available. The kit runs it now rather
    #     than deferring for a free refill, because `cash == 0` means no new
    #     money and because a reset time is not a proof of availability. We keep
    #     that order, and reverse it only under the condition below.
    if included_sub:
        chosen = included_sub[0]
        check = tighten_for_model(floor, chosen, family)
        rationed = (chosen.get("allocation_remaining") is not None
                    and chosen["allocation_remaining"] - chosen["allocation"]
                    < chosen.get("reserve_high_impact", 0.0))
        if (rationed and req["can_wait"] and waiting_free
                and use == "internal_dashboard"):
            wake = waiting_free[0]
            return decision(
                "defer", req, floor, resource=wake, calls=[],
                wake_in_minutes=wake["reset_minutes"],
                priority="defer_before_included",
                reason=(f"{family} {plan['label']}, {USES[use]}: reversal of the kit's "
                        f"order. The included allocation of {chosen['id']} left after this "
                        f"call ({round(chosen['allocation_remaining'] - chosen['allocation'], 6)} "
                        f"USD) would fall below the "
                        f"{chosen['reserve_high_impact']} USD reserved for customer-facing "
                        f"and payout traffic, the request can wait and {wake['id']} refills "
                        f"in {wake['reset_minutes']} min, inside the "
                        f"{req['deadline_minutes']} min deadline with a "
                        f"{WAKE_MARGIN_MINUTES} min margin to re-measure availability and "
                        f"pay for one retry. {td1_quote(wake, family)}. Availability is "
                        f"re-measured at wake-up: a reset time is not a proof of capacity"))
        reason = (f"{family} {plan['label']}, {USES[use]}: no free route available, "
                  f"{chosen['id']} is included subscription capacity (cash 0, allocation "
                  f"{chosen['allocation']} USD of a fee already paid), so it runs now "
                  f"rather than waiting for a refill that a reset time does not guarantee. "
                  f"{td1_quote(chosen, family)}. Check {check}.")
        if check != floor:
            reason += f" Check tightened from {floor} to {check}: this route has no TD 1 cell."
        return decision("run", req, check, resource=chosen, reason=reason,
                        priority="included_before_defer")

    # 4. Wait for a free route to refill, when the request can wait.
    if waiting_free and req["can_wait"]:
        wake = min(waiting_free, key=lambda r: r["reset_minutes"])
        return decision("defer", req, floor, resource=wake, calls=[],
                        wake_in_minutes=wake["reset_minutes"],
                        reason=(f"{family} {plan['label']}, {USES[use]}: every eligible route is "
                                f"rate-limited; {wake['id']} refills in {wake['reset_minutes']} min, "
                                f"inside the {req['deadline_minutes']} min deadline with a "
                                f"{WAKE_MARGIN_MINUTES} min margin. {wake['limit_td1']}. "
                                f"{td1_quote(wake, family)}. Availability is re-measured at "
                                f"wake-up: reaching a reset time does not prove capacity"))

    # 5. New money, last. Spending here is preferred to answering free with a
    #    model that erred on the family, and to a panel improvised out of such
    #    models: on C02 gpt-oss-20b and dots both return 0 instead of 590320, so
    #    a vote between the weak models of a family can agree on a wrong value.
    if paid:
        chosen = paid[0]
        check = tighten_for_model(floor, chosen, family)
        refused = [f"{r['id']} ({td1_quote(r, family)})" for r in resources
                   if r["available"] and r["cash"] == 0 and r["allocation"] == 0
                   and not is_perfect(r, family)]
        return decision("run", req, check, resource=chosen,
                        free_routes_refused=refused or None,
                        reason=(f"{family} {plan['label']}, {USES[use]}: no eligible included "
                                f"capacity; {chosen['id']} is a documented billed route of the "
                                f"exact same model as our measured one, so the TD 1 cells "
                                f"transfer ({td1_quote(chosen, family)}). "
                                f"{chosen['cash']} USD excl. tax per request on the "
                                f"{ENVELOPE['input_tokens']}/{ENVELOPE['output_tokens']} token "
                                f"envelope, inside the {req['budget']} USD budget. Check {check}. "
                                f"Free routes still up were refused rather than voted together: "
                                f"{'; '.join(refused) if refused else 'none available'} - on C02 "
                                f"gpt-oss-20b and dots both answer 0 instead of 590320, so a "
                                f"panel improvised from the models that erred on the family can "
                                f"agree on a wrong value"))

    # 6. Abstain rather than answer without the required check.
    return decision("abstain", req, floor,
                    f"{family} {plan['label']}, {USES[use]}: no eligible route available "
                    f"inside the {req['deadline_minutes']} min deadline and the "
                    f"{req['budget']} USD budget. The rule abstains instead of answering "
                    f"with a model that erred on {plan['cases']} in TD 1 or without the "
                    f"{floor} check. {quorum_note}".strip())


def normalise(request: dict) -> dict:
    """Accept our requests (family, use) and the kit's (difficulty, high_impact)."""
    req = dict(request)
    if "family" not in req:
        req["family"] = DIFFICULTY_TO_FAMILY.get(req.get("difficulty"), "unmeasured")
    if "use" not in req:
        req["use"] = "payout" if req.get("high_impact") else "internal_dashboard"
    req.setdefault("can_wait", True)
    req.setdefault("deadline_minutes", 120)
    req.setdefault("budget", 0.30)
    return req


# --------------------------------------------------------------------------
# Scenarios. The first seven are the kit's, mapped onto family/use so the
# before/after outputs can be read side by side; the rest exercise our rule.
# --------------------------------------------------------------------------
def scenarios():
    base = {"difficulty": 1, "high_impact": False, "can_wait": True,
            "deadline_minutes": 120, "budget": 0.30}
    # Groq per-minute limits: the TD 1 429s cleared within a minute, so a
    # rate-limited free route is modelled as refilling in 1 minute.
    groq_exhausted = [dict(r, available=False, reset_minutes=1)
                      if r["id"].startswith("groq:") else dict(r) for r in RESOURCES]
    all_free_exhausted = [dict(r, available=False, reset_minutes=1)
                          if r["access"] == "free" else dict(r) for r in RESOURCES]
    free_gone_no_refill = [dict(r, available=False, reset_minutes=None)
                           if r["access"] == "free" else dict(r) for r in RESOURCES]
    # Same situation, but the subscription has almost nothing left above the
    # share reserved for customer-facing and payout traffic.
    sub_rationed = [dict(r, allocation_remaining=0.0150) if r["access"] == "subscription"
                    else dict(r) for r in all_free_exhausted]
    only_measured_gone = [dict(r, available=False, reset_minutes=None)
                          if r["id"] in ("groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b")
                          else dict(r) for r in RESOURCES]
    return [
        # --- the kit's seven, with its own request shape ---
        ("simple", base, RESOURCES),
        ("complex", {**base, "difficulty": 3}, RESOURCES),
        ("deferrable", {**base, "difficulty": 3}, groq_exhausted),
        ("urgent", {**base, "difficulty": 3, "can_wait": False, "deadline_minutes": 5}, groq_exhausted),
        ("budget exhausted", {**base, "difficulty": 3, "can_wait": False, "budget": 0}, free_gone_no_refill),
        ("high impact", {**base, "difficulty": 3, "high_impact": True}, RESOURCES),
        ("unknown capability", {**base, "difficulty": 4}, RESOURCES),
        # --- our rule, one line per family and per cost of error ---
        ("F1 period / dashboard",
         {"family": "F1", "use": "internal_dashboard"}, RESOURCES),
        ("F1 period / customer",
         {"family": "F1", "use": "customer_facing"}, RESOURCES),
        ("F2 age at a date / dashboard",
         {"family": "F2", "use": "internal_dashboard"}, RESOURCES),
        ("F2 age at a date / customer",
         {"family": "F2", "use": "customer_facing"}, RESOURCES),
        ("F2 age at a date / payout",
         {"family": "F2", "use": "payout"}, RESOURCES),
        ("F2b age at the order / dashboard",
         {"family": "F2b", "use": "internal_dashboard"}, RESOURCES),
        ("F2b age at the order / payout",
         {"family": "F2b", "use": "payout"}, RESOURCES),
        ("F3 product list / dashboard",
         {"family": "F3", "use": "internal_dashboard"}, RESOURCES),
        ("F4 combined / customer",
         {"family": "F4", "use": "customer_facing"}, RESOURCES),
        ("F4 combined / payout",
         {"family": "F4", "use": "payout"}, RESOURCES),
        # --- availability, deferral, money, abstention ---
        ("F2 first model unavailable",
         {"family": "F2", "use": "internal_dashboard"}, only_measured_gone),
        ("F2 every free route rate-limited, can wait",
         {"family": "F2", "use": "internal_dashboard", "deadline_minutes": 30},
         all_free_exhausted),
        ("F2 every free route rate-limited, urgent",
         {"family": "F2", "use": "customer_facing", "can_wait": False, "deadline_minutes": 1},
         all_free_exhausted),
        ("F2b included before defer",
         {"family": "F2b", "use": "internal_dashboard", "deadline_minutes": 30},
         all_free_exhausted),
        ("F2b defer before included (reversal)",
         {"family": "F2b", "use": "internal_dashboard", "deadline_minutes": 30}, sub_rationed),
        ("F2b included before defer, payout",
         {"family": "F2b", "use": "payout", "deadline_minutes": 30}, sub_rationed),
        ("F4 quorum impossible, free routes gone",
         {"family": "F4", "use": "customer_facing", "can_wait": False, "budget": 0.0},
         free_gone_no_refill),
    ]


# --------------------------------------------------------------------------
# Output and self-checks.
# --------------------------------------------------------------------------
def print_rule() -> None:
    print("| Family | TD 1 cells | TD 1 rate (5 models) | First call (cheapest correct) | "
          "Dashboard | Customer | Payout | If unavailable |")
    print("|---|---|---|---|---|---|---|---|")
    for key, plan in RULE.items():
        order = preference_order([r for r in RESOURCES if is_perfect(r, key)], key)
        first = order[0]["id"] if order else "none: no model is 100 %"
        rest = ", ".join(r["id"] for r in order[1:]) or "defer, then billed route, then abstain"
        print(f"| {key} {plan['label']} | {plan['cases']} | {plan['pooled']} | {first} | "
              f"{plan['check']['internal_dashboard']} | {plan['check']['customer_facing']} | "
              f"{plan['check']['payout']} | {rest} |")


def check_rates() -> int:
    """Verify the TD 1 numbers embedded above against the generated CSV."""
    if not RATES_CSV.exists():
        print(f"missing {RATES_CSV}: run td2/C/scripts/family_rates_td2.py first")
        return 1
    with RATES_CSV.open(encoding="utf-8-sig", newline="") as handle:
        generated = {(row["family"], row["model_id"]): (int(row["correct"]), int(row["total"]))
                     for row in csv.DictReader(handle)}
    problems = 0
    for resource in RESOURCES:
        if not resource["td1"]:
            continue
        # A billed route inherits the cells of the exact same model it bills.
        measured_id = resource.get("rates_from", resource["id"])
        for family, measured in resource["td1"].items():
            expected = generated.get((family, measured_id))
            if expected is None:
                print(f"no CSV row for {family} {measured_id}")
                problems += 1
                continue
            if (measured["correct"], measured["cases"]) != expected:
                print(f"MISMATCH {family} {resource['id']}: embedded "
                      f"{measured['correct']}/{measured['cases']}, CSV {expected[0]}/{expected[1]}")
                problems += 1
    print("embedded TD 1 rates agree with td2/C/analysis/csv/family-rates-td1.csv"
          if not problems else f"{problems} mismatch(es)")
    return 1 if problems else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", help="show only the named scenario")
    parser.add_argument("--table", action="store_true", help="readable table instead of JSON lines")
    parser.add_argument("--rule", action="store_true", help="print the rule as a markdown table")
    parser.add_argument("--check-rates", action="store_true",
                        help="verify the embedded TD 1 rates against the generated CSV")
    args = parser.parse_args()

    if args.rule:
        print_rule()
        return
    if args.check_rates:
        raise SystemExit(check_rates())

    found = False
    rows = []
    for name, request, resources in scenarios():
        if args.scenario and name != args.scenario:
            continue
        found = True
        result = choose(request, resources)
        rows.append((name, normalise(request), result))
        if not args.table:
            print(json.dumps({"scenario": name, "nature": "simulation",
                              "request": normalise(request), "result": result}))
    if not found:
        parser.error("unknown scenario")
    if args.table:
        print(f"{'scenario':38s} {'action':8s} {'resource':34s} {'check':12s} "
              f"{'calls':5s} {'cash':9s} reason")
        for name, request, result in rows:
            print(f"{name:38s} {result['action']:8s} {str(result['resource']):34s} "
                  f"{result['check']:12s} {len(result['calls']):<5d} "
                  f"{result['cash']:<9} {result['reason'][:110]}")


if __name__ == "__main__":
    main()
