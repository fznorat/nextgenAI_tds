# TD 2 — Cross-review by pair A of pair C (Step 3, routing rule)

Reviewer: pair A (PERKINS Luca). Session of 18 November 2026. Reviewed: [`../C/README.md`](../C/README.md) (sections 3.1 to 3.8 of the report) and the files of [`../C/`](../C/) at commit `4542736`. The kit's `atelier-routage.py` is the reference for `choose`.

Declaration: the review was prepared with Claude's help. The re-runs are in [`outputs/review/rerun-b-c-scripts.txt`](outputs/review/rerun-b-c-scripts.txt) and [`outputs/review/review_check_output.txt`](outputs/review/review_check_output.txt); the independent checks are in [`scripts/review_check.py`](scripts/review_check.py).

## Reproduced?

Yes, from the merged traces `td1/data/traces/traces-td1.csv` and the student kit, no model call:

- **All 25 cells of the family-rate table match** our independent recount (5 families × 5 models), with the pooled totals 30/30, 12/20, 2/5, 19/20, 17/25.
- `family_rates_td2.py` regenerates the two CSV files with the same content as committed (only the line endings differ).
- `age_guard_td2.py <kit>`: **the check reproduces the reference on 20/20 questions** and rejects exactly C10 (−439570) and C15 (−168680).
- `atelier-routage.py` (before) and `atelier-routage-td2.py` (after) give outputs **identical** to `routage-before.jsonl` and `routage-after.jsonl`; `--check-rates` confirms the embedded rates agree with the CSV.
- Measured facts: 20 failed cells of which 19 carry an age clause (the exception is Qwen's C12); HTTP 429 on gpt-oss-20b C19 and Qwen C16–C20; medians **626 / 140** tokens; reasoning counter above 0 on 40 rows and never above the completion tokens; gpt-oss-20b **0.0000890** and gpt-oss-120b **0.0001779** USD per request at 0.075 / 0.30 and 0.15 / 0.60 USD per million.
- Their quorum table (3.2) agrees with ours on all 20 questions for both quorums: **0 differences**.
- 3.6 matches the source of `choose`: the `included` branch (`available` and `cash == 0`) returns before `waiting` is evaluated, and inside it the key `(allocation, level, id)` takes a free resource before a subscription.

## Two things that are solid

1. **Every claim is tied to a cell and to a cost of error.** For each family the rule gives the cells, the ratio per model, the first model, the check per use and the fallback, and the consistency constraint is applied honestly (`none` only for a dashboard on a family where the called model scored 100 %). Refusing `none` on F4 despite 5/5 for gpt-oss-20b is explicitly labelled a judgement, not a measurement.
2. **The priority analysis is exact and goes further than the answer.** It reads the branch order of `choose`, gives three reasons for preferring included capacity (no new money, deferring buys an uncertain gain, a free resource still wins inside the branch), and states a concrete operational condition that reverses it, demonstrated by scenarios. Section 3.7 names the same-family weakness of gpt-oss-120b / 20b, and the deterministic check is executed, not only described.

## Remaining remarks

1. **Price source.** The page asks for "the cheapest according to the portfolio". The portfolio CSV of 28 September lists gpt-oss-20b and Qwen 3.8-27b only as free Groq routes, with no paid price; the 120b price (0.15 / 0.60) is in the CSV on the OpenRouter row. The prices of the 20b and of Qwen, which decide the first call of F1, F2b, F3 and F4, come from "Groq Developer prices of 5 October 2026", given without a link. Give the source (URL or file), or say which rows of the rule depend on a price outside the portfolio.
2. **In-sample result.** "Panels built per family beat one fixed panel" (3.2, reading 3) is true by construction: the panels are chosen from the same twenty questions that then score them. Say "on this batch, by construction" there, as section 3.7 already does for the rule.
3. **A scenario departs from "levels come from TD 1".** In "budget exhausted" the rule runs `codex:gpt-5.6-luna`, which has no TD 1 cell. The justification (admissible only behind the deterministic check) is reasonable; put it in the rule table as well as in the scenario list.

Verdict: rates, costs, reading of `choose`, the executed check and the simulator outputs are correct and reproducible. Only the price source and two wordings should be fixed before hand-in.
