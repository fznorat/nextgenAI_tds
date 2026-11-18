# TD 2, Review by pair B of pair A's work (Step 1, the k-of-n vote)

Reviewers: SAAID Myriam, DE GENTILE Océane (pair B). Reviewed: [`../A/README.md`](../A/README.md), [`../A/scripts/skeleton-multi-llm-en.py`](../A/scripts/skeleton-multi-llm-en.py), [`../A/scripts/step1_table.py`](../A/scripts/step1_table.py), [`../A/analysis/csv/step1-table.csv`](../A/analysis/csv/step1-table.csv).

Declaration: review prepared with the help of Claude; the checks listed in the table below were re-run by pair B.

## What we checked, and how

| Check | Result |
|---|---|
| Re-ran `step1_table.py` on `td1/data/traces/traces-td1.csv` and compared with the committed CSV | Identical, 20/20 rows |
| Re-ran `atelier-vote.py` (four synthetic examples) | As specified: agreement → 100; disagreement → abstain (1 vote); unavailable → abstain (1 vote); wrong consensus `[0, 0, 100]` → 0 |
| Compared pair A's votes with pair B's independent count on the four shared wrong values (C02, C08, C10, C15), 2-of-3 and 3-of-5 | 8/8 identical (output in [`outputs/wrong-consensus/pair_b_output.txt`](outputs/wrong-consensus/pair_b_output.txt)) |
| Edge cases run on `vote_k_sur_n` | `0` counts as a value (consensus on 0); a proposal with `verdict = error` does not vote even if it carries a value; k = 2 of 4 and an empty panel raise `ValueError`; three unavailable members → abstain with 0 votes |

## Assessment

- The contract of the docstring is respected point by point: strict majority checked before anything else, duplicates refused, unavailable members kept in n without a vote, no value invented, the reference never passed to the vote.
- The table is correct and the three decisions that change between 2-of-3 and 3-of-5 (C02, C15, C19) are explained with the exact values and verdicts.
- The link with step 2 is consistent: the only wrong consensus that survives 3-of-5 is C10, which is the case pair B analyses.

## Remarks

1. `A/README.md` still says "add the second member here": to complete before hand-in.
2. Suggestion: state in the README that the panel members' order does not matter (the vote counts values, it does not use positions), since two values cannot both reach a strict majority.
3. Point to keep in mind for the quiz: 3-of-5 is not "safer" in general; on our batch it removes one wrong consensus (C15) but loses one correct answer (C02) and changes nothing on C10.
