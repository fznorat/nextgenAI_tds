# TD 3 report — configuration, cost and demonstration

Session: 2 December 2026. Kit: see the pack published for the session.
Sub-group 3 (DIA 1).

**Status: not started.** This file is the folder's placeholder and its plan. It is filled during
TD 3; nothing below is a result.

## 0. What this folder will hold

| Planned file | What it will be |
|---|---|
| `td3.md` | This report: configuration retained, cost per request, annual projection, demonstration, limitations, contributions |
| `analysis/csv/cost-calculation.csv` | The three quantities of the cost method, kept in separate columns: real spend, API-equivalent cost, cost charged to a subscription |
| `analysis/csv/configuration-comparison.csv` | Single model, 2-of-3 quorum, 3-of-5 quorum and our routing rule, compared on cases handled, abstentions, errors, calls and cost |
| `scripts/` | Scripts that compute the above from the committed TD 1 traces |
| `outputs/` | Saved outputs and the demonstration trace |

## 1. What TD 2 hands over

The routing rule and its evidence are in [`../td2/td2.md`](../td2/td2.md). Three results of TD 2
decide what TD 3 has to price:

1. **Checking is the cost driver, not the model.** On our batch every model call is free or costs
   fractions of a cent on the envelope of 626 input / 140 output tokens: 0.0000890 USD excl. tax for
   `gpt-oss-20b`, 0.0001779 for `gpt-oss-120b`, 0.0010608 for `qwen3.8-27b`. A 3-of-5 quorum
   multiplies the calls by five; the deterministic reference check adds one local SQL execution and
   no model call at all.
2. **No quorum cost on our panel can be complete.** `cohere/north-mini-code:free` and
   `dots-3-note-preview:free` have no documented paid route of the exact same model, so the
   API-equivalent of a 3-of-5 quorum is **N/A with coverage 3/5 calls priced** (known subtotal
   0.0013277 USD excl. tax). TD 3 must either state that N/A with its coverage or replace those two
   routes with priceable ones — it must not project the subtotal as the total.
3. **Three questions set the price of checking**: `C10` (age at the time of the order), `C15` and
   `C17` (combined filters). On C10 both the fixed 2-of-3 panel and the 3-of-5 quorum return 119410
   instead of 558980, so on that family the cheapest adequate check is a deterministic
   recomputation, not a bigger panel.

## 2. Planned work

- Compute, per configuration, the three quantities of `methode-cout-en.md` on the TD 1 traces, with
  retries counted and every assumption written down.
- Divide a complete equivalent by the number of requests handled, and state abstentions and errors
  next to it: a cheaper configuration that abstains more does not deliver the same service.
- Project to a company volume (for example 20 people × 10 requests/day × 20 days × 12 months =
  48 000 requests/year) and show which part of the bill comes from the configuration rather than
  from the volume.
- Demonstrate the rule end to end on a handful of questions, with the trace of each decision and its
  reason.
- Record what the computation does **not** give: a provider invoice, an error rate per model, or the
  cost of the human work around the system.

## 3. Contributions

To be completed during the session.
