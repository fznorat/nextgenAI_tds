# TD 2, Review by pair B of pair C's work (Step 3, the routing rule)

Reviewers: SAAID Myriam, DE GENTILE Océane (pair B). Reviewed: [`../C/README.md`](../C/README.md), [`../C/outputs/routing/rule-table.md`](../C/outputs/routing/rule-table.md), [`../C/scripts/`](../C/scripts/).

Declaration: review prepared with the help of Claude; the checks listed in the table below were re-run by pair B.

## What we checked, and how

| Check | Result |
|---|---|
| `atelier-routage-td2.py --check-rates` | "embedded TD 1 rates agree with `family-rates-td1.csv`" |
| `age_guard_td2.py` on `data/boutique.sqlite` | Reproduces the reference on 20/20 questions; rejects 119410 on C10 in both quorums (−439570 cents) and 0 on C15 (2-of-3) |
| Consistency constraint ("none" only for the dashboard AND on a family where the first model is 100 % in TD 1) | Respected: F1 and F3 start with gpt-oss-20b (6/6 and 4/4), F2 with gpt-oss-120b (4/4; 20B fails C02 and C11); F2b and F4 never use "none" |
| Link with step 2 | Consistent: C10 (F2b) is the shared wrong value of pair B; the rule requires `reference` for every use on F2b, which is exactly what the delta query justifies (439570 cents missed by three models from three providers) |

## Assessment

- Every choice refers back to TD 1 cells and rates, and every check to a cost of error (dashboard / customer / payout).
- The conclusion of section 8 matches ours: on C10 the cheapest adequate check is a deterministic recomputation, not a larger quorum.

## Remarks

1. **F2, figure shown to a customer: `quorum_2of3`.** It is justified by the batch (the fixed panel is right on C02, C08, C09 and C11), but F2 is an age family and our step 2 shows that the same age-logic gap is shared across providers (C10, and C15 in F4). We also found that Dots omits the same case (b) on C15 (29760 cents missed, customers C005 and C007, see [`scripts/delta_c15_dots.sql`](scripts/delta_c15_dots.sql)): the gap on age logic is not isolated. We would discuss using `reference` for customer-facing F2 figures too: the check already exists (`age_guard_td2.py`) and costs no model call.
2. **Broken links in the main report** [`../README.md`](../README.md), section 3: it still points to `scripts/...`, `outputs/routing/...` and `analysis/csv/...` at the root of `td2/`, which were moved to `td2/C/`. Replace section 3 by a summary linking to `C/README.md`, as pairs A and B did.
3. Twenty questions support a batch-specific rule, not a general error rate: already stated in section 7, worth repeating in the plenary.
