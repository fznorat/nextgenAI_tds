# TD 2 — Pair C: Step 3, the routing rule

Session: 18 November 2026. Sub-group 3 (DIA 1). Author: VERDES Adrian (pair C; add the second member here).

**No new provider call was made.** All figures come from the 100 real TD 1 cells in
[`../../td1/data/traces/traces-td1.csv`](../../td1/data/traces/traces-td1.csv) and from the final
verdict of each cell in
[`../../td1/analysis/csv/model-question-comparison-en.csv`](../../td1/analysis/csv/model-question-comparison-en.csv).

**Nature of the data:** real TD 1 traces (`nature = real`, final attempt per model and question). The
simulator's availabilities, reset times and capability levels are **supplied by a scenario**, labelled
`"nature": "simulation"` on every output line, and are never measured from a provider. Model letters
A–E are the TD 1 models, not the session pairs: A = `openai/gpt-oss-120b`, B = `openai/gpt-oss-20b`,
C = `cohere/north-mini-code:free`, D = `qwen/qwen3.8-27b`, E = `dots-studio/dots-3-note-preview:free`.

**Declaration:** the three scripts in this folder were written with Claude's help; pair C read them,
ran them and checked their outputs against the committed TD 1 files. `--check-rates` re-verifies the
TD 1 numbers embedded in the simulator against the generated CSV, and the deterministic check is
validated against all twenty references (section 4). No figure in this folder comes from a model
answer.

## What is in this folder

| File | What it is |
|---|---|
| [`scripts/family_rates_td2.py`](scripts/family_rates_td2.py) | Derives the exact `correct / cases` rate of every question family per model, and what a fixed 2-of-3 panel, a 3-of-5 quorum and per-family panels would have returned. Writes the two CSV files below. |
| [`analysis/csv/family-rates-td1.csv`](analysis/csv/family-rates-td1.csv) | Rate per family and per model, with every failing cell named |
| [`analysis/csv/quorum-by-family-td1.csv`](analysis/csv/quorum-by-family-td1.csv) | One row per question: decision, value, votes and agreement with the reference, for the three configurations |
| [`scripts/atelier-routage.py`](scripts/atelier-routage.py) | The kit's simulator, **byte-identical copy**, kept so the "before" output can be reproduced |
| [`scripts/atelier-routage-td2.py`](scripts/atelier-routage-td2.py) | The simulator adapted to our rule: our models, per-family eligibility from TD 1, portfolio prices, checks derived from the family and the cost of an error, TD 1 cells in every reason |
| [`scripts/age_guard_td2.py`](scripts/age_guard_td2.py) | The deterministic check the rule calls `reference`, executed on `data/boutique.sqlite` |
| [`outputs/routing/`](outputs/routing/) | Saved outputs: before, after, the rule table, the family rates, the check on the twenty questions |
| `groupe-A.md`, `groupe-B.md` | Cross-review of this work by pairs A and B. **Not written by pair C** |

**Reproduce** from the repository root:

```powershell
python td2/C/scripts/family_rates_td2.py --print
python td2/C/scripts/atelier-routage.py                      # before
python td2/C/scripts/atelier-routage-td2.py --table          # after
python td2/C/scripts/atelier-routage-td2.py --rule           # the rule as a table
python td2/C/scripts/atelier-routage-td2.py --check-rates    # embedded rates vs the CSV
python td2/C/scripts/age_guard_td2.py <student-kit-dir>      # the reference check on C01..C20
```

`<student-kit-dir>` is the local student kit holding `data/boutique.sqlite`; the database is supplied
by the course and is not committed.

---

## 1. The exact TD 1 rate of each family

Families are the question types of `questions-td1-en.md`. The rates are regenerated from the
100-cell comparison table, never hand-typed; `--check-rates` verifies that the numbers embedded in
the simulator still match the CSV.

| Family | TD 1 cells | gpt-oss-120b | gpt-oss-20b | cohere north-mini | qwen3.8-27b | dots-3-note | Pooled |
|---|---|---|---|---|---|---|---|
| **F1** period | C01, C04, C05, C06, C07, C20 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | **30/30** |
| **F2** completed age on a reference date | C02, C08, C09, C11 | **4/4** | 2/4 | 0/4 | **4/4** | 2/4 | **12/20** |
| **F2b** age at the time of the order | C10 | 1/1 | 1/1 | 0/1 | 0/1 | 0/1 | **2/5** |
| **F3** product list | C03, C12, C13, C14 | 4/4 | 4/4 | 4/4 | 3/4 | 4/4 | **19/20** |
| **F4** combined filters | C15, C16, C17, C18, C19 | 4/5 | **5/5** | 3/5 | 2/5 | 3/5 | **17/25** |

Failing cells, from the CSV:

- **F2** — 20b: C02 returns 0 (window of age 0), C11 returns 322160 (ages 20 to 24). cohere: C02
  `sql_invalid`, C08/C09/C11 return 0. dots: C02 and C08 return 0.
- **F2b** — cohere, qwen and dots all return 119410 on C10.
- **F3** — qwen: C12 `sql_rejected`, an unclosed ```` ```sql ```` fence. A format failure, but a lost
  cell all the same.
- **F4** — 120b: C19 returns 0. cohere: C15 returns 0, C17 returns 197080. qwen: C15 returns 0, C17
  returns 248490, C19 returns 83580. dots: C15 returns 138920, C17 `sql_invalid`.

**The one fact the whole rule rests on:** 19 of the 20 failed cells carry an age clause. The period
and product clauses cost us nothing in this batch (F1 30/30, F3 19/20, and the single F3 loss is a
formatting accident, not a logic error). So the rule is cheap where there is no age, and
deterministic where there is.

Note on the denominators: a scalar "capability level" cannot carry this rule. `gpt-oss-20b` is 5/5 on
F4 but 2/4 on F2; `qwen3.8-27b` is 4/4 on F2 but 2/5 on F4. Eligibility is therefore stored per
family in the simulator, not as one number per model.

## 2. What a vote would have returned (cross-check for pair A)

Pair A's README refers to this table as "section 3.2": it is section 2 of this file, since the TD 2
report was split into one folder per pair after it was first written.

Pair C needed the quorum outcomes to justify the checking column of the rule, so it implemented the
same contract independently (`vote_k_of_n` in
[`scripts/family_rates_td2.py`](scripts/family_rates_td2.py)) and ran it on the same 100 cells. Full
table in [`analysis/csv/quorum-by-family-td1.csv`](analysis/csv/quorum-by-family-td1.csv). Fixed
panel = `gpt-oss-120b`, `cohere/north-mini-code:free`, `qwen3.8-27b` with k = 2 (the panel of
`atelier-vote.py`). Quorum = the five TD 1 models with k = 3. A cell with no value (`sql_invalid`,
`sql_rejected`) stays in n and casts no vote.

**Cross-check result:** compared cell by cell with pair A's table (decision, value and votes, both
columns, twenty questions), **0 differences**. Two independent implementations on the same cells give
the same decisions. Pair A's table is the step 1 deliverable; this one exists to price the checks.

Reference / wrong / abstention, per family:

| Family | Fixed 2-of-3 | 3-of-5 | Our rule's per-family panels |
|---|---|---|---|
| F1 (6) | 6 / 0 / 0 | 6 / 0 / 0 | 6 / 0 / 0 |
| F2 (4) | 4 / 0 / 0 | 3 / 0 / 1 | 4 / 0 / 0 |
| F2b (1) | 0 / **1** / 0 | 0 / **1** / 0 | 0 / 0 / 1 (no panel admissible) |
| F3 (4) | 4 / 0 / 0 | 4 / 0 / 0 | 4 / 0 / 0 |
| F4 (5) | 2 / **1** / 2 | 3 / 0 / 2 | 3 / 0 / 2 |
| **All 20** | 16 / **2** / 2 | 16 / **1** / 3 | **17 / 0 / 3** |

Three readings drive the rule:

1. **A larger quorum is not uniformly safer.** Going from 2-of-3 to 3-of-5 removes the wrong
   consensus on C15 (0 instead of 168680, because cohere and qwen agree on 0 inside the fixed panel)
   but turns a correct answer into an abstention on C02 (590320 gets 2 votes, 0 gets 2 votes from 20b
   and dots, and cohere casts no vote at all because its SQL is invalid). It changes which error you
   make, not whether you make one.
2. **On F2b no quorum works.** Both configurations return 119410 instead of 558980, a gap of
   −439570 cents. The only 2-of-3 panel that returns the reference is
   `gpt-oss-120b + gpt-oss-20b + anything`, i.e. two members of the **same** model family — the
   configuration lecture 2 tells us not to buy safety with, because models trained on close data are
   wrong together. C10 is that lecture, measured on our own batch.
3. **Panels built per family beat one fixed panel.** Choosing members among the models TD 1 shows
   correct on that family, keeping three distinct model families and two providers, gives 17 / 0 / 3
   over the twenty questions: no wrong value anywhere, against 2 for the fixed panel and 1 for the
   3-of-5 quorum.

The SQL cause of the C10 consensus and its delta query are pair B's deliverable
([`../B/`](../B/)).

---

## 3. The rule (one page)

**Principle.** The question's family sets who is called; the cost of an error sets what checks the
answer. An age clause is the only thing that failed in our batch, so an age clause is the only thing
that pays for a deterministic check. `none` is never used where the model called erred on the
family, nor on a figure shown to a customer, nor on an amount paid out.

**Prices.** USD excluding tax per request on one fixed envelope — 626 input and 140 output tokens,
the medians of the 100 executed TD 1 cells. Groq Developer prices of 5 October 2026; portfolio
snapshot of 28 September 2026. Reasoning tokens are included in `tokens_completion` on Groq
(checked: `completion >= reasoning` on all 40 rows that carry the counter), so they are not added.
`cohere/north-mini-code:free` and `dots-3-note-preview:free` have **no documented paid route of the
exact same model**: their equivalent is **N/A, which is not 0**.

| Route | Access | Cash at request time | API equivalent, same model |
|---|---|---:|---:|
| `groq:openai/gpt-oss-20b` | free | 0 | 0.0000890 |
| `groq:openai/gpt-oss-120b` | free | 0 | 0.0001779 |
| `groq:qwen/qwen3.8-27b` | free | 0 | 0.0010608 |
| `openrouter:cohere/north-mini-code:free` | free | 0 | N/A |
| `openrouter:dots-studio/dots-3-note-preview:free` | free | 0 | N/A |
| `groq-developer:openai/gpt-oss-120b` | paid | 0.0001779 | 0.0001779 |
| `codex:gpt-5.6-luna` | subscription | 0 (allocation 0.0000211) | 0.0002932 |

At request time every free route costs 0, so "the cheapest one" is decided by the price the portfolio
*does* document for the exact same model (what this configuration would cost a company), then by the
rate-limit friction measured in TD 1 (qwen: 5 × HTTP 429 on C16–C20, OTPM 1000; 20b: 1 × HTTP 429 on
C19, TPM 8000), then by median latency (Groq 0.4–0.8 s, OpenRouter free 2.4–2.8 s). A route whose
billed equivalent is N/A cannot be called the cheapest, so it ranks last among equals.

### The rule, family by family

| Family | TD 1 cells and rate | First call (cheapest correct on the family) | Internal dashboard | Figure shown to the customer | Amount paid out | If the first model is unavailable |
|---|---|---|---|---|---|---|
| **F1** period | C01,C04,C05,C06,C07,C20 — every model 6/6, pooled 30/30 | `gpt-oss-20b` (free, 0.0000890, cheapest documented equivalent, 6/6) | **none** — admissible: 6/6 on the family *and* low stakes | **2-of-3** on {120b, qwen, dots} — 6/6 on our traces | **reference** + human review | 120b → qwen → cohere → dots (all 6/6) → billed 120b (0.0001779) → defer → abstain |
| **F2** completed age at a date | C02,C08,C09,C11 — 120b 4/4, qwen 4/4, 20b 2/4, dots 2/4, cohere 0/4, pooled 12/20 | `gpt-oss-120b` (free, 4/4; cheaper than qwen's 0.0010608 and its 5 × 429) | **none, but only with 120b or qwen.** Any other model erred on C02, C08, C09 or C11 → the check tightens to 2-of-3 | **2-of-3** on {120b, qwen, dots} — 4/4 on our traces, where the 3-of-5 abstains on C02 | **reference** + human review | qwen (4/4) → billed 120b → defer for the Groq refill → abstain. **Never** 20b, cohere or dots alone, and **never** a vote among them: on C02 20b and dots both answer 0 |
| **F2b** age at the time of the order | C10 — 120b 1/1, 20b 1/1, cohere/qwen/dots 0/1, pooled 2/5 | `gpt-oss-20b` (free, cheapest of the two correct) behind the check | **reference** | **reference** | **reference** + human review | 120b → billed 120b → subscription behind the same check → defer → abstain |
| **F3** product list | C03,C12,C13,C14 — 120b, 20b, cohere, dots 4/4, qwen 3/4, pooled 19/20 | `gpt-oss-20b` (free, 4/4, cheapest) | **none** — 4/4 on the family and low stakes | **2-of-3** on {120b, cohere, dots} — 4/4 on our traces | **reference** + human review | 120b → cohere → dots → billed 120b → abstain. qwen last: C12 `sql_rejected` |
| **F4** combined filters | C15–C19 — 20b 5/5, 120b 4/5, cohere 3/5, dots 3/5, qwen 2/5, pooled 17/25 | `gpt-oss-20b` (free, 5/5), inside the quorum | **3-of-5** | **3-of-5** | **reference** + human review | defer for a refill → billed 120b → abstain. A quorum that cannot reach k is replaced by the reference check, not by a thinner vote |

**Why F2b takes no vote at any stake.** On C10 the fixed 2-of-3 panel returns 119410 with 2 votes of
3, and the 3-of-5 quorum returns 119410 with 3 votes of 5 — both wrong by 439570 cents. A check that
is a second opinion cannot catch an error the panel shares. The check must recompute the answer from
the question, which is what section 4 does.

**Why F4 refuses `none` even though `gpt-oss-20b` is 5/5 there.** The consistency constraint allows
`none` for a low-stakes dashboard on a family where the model called scored 100 %, and 5/5 on
C15–C19 satisfies its letter. We refuse it anyway, and this is a judgement, not a measurement: four
of the five models erred on this family (pooled 17/25), the evidence for 20b is five cells of one run
at temperature 0, the fixed panel returned a wrong value on C15, and all five routes are free — so
the quorum costs quota and latency, not money. Where a check is nearly free and the family is the
second most fragile in the batch, we buy it.

**The three uses, and what an error costs.**

- *Internal dashboard* — an error is read by a colleague who can sanity-check it; the cost is lost
  time. `none` is acceptable where the family never failed for that model.
- *Figure shown to the customer* — an error is published and must be retracted; the cost is
  credibility. A quorum is the floor, and its abstention is a feature: no figure is better than a
  wrong figure.
- *Amount paid out* — an error moves money. Only the deterministic check plus a human review is
  admissible, on every family including those where every model scored 100 %: F1 is 30/30 in a batch
  of six questions, which bounds nothing about the next question.

**What the checking costs** (API equivalent per request, same envelope):

| Check | Model calls | Cost |
|---|---:|---|
| `none` | 1 | 0.0000890 (20b) or 0.0001779 (120b) |
| 2-of-3, F1/F2 panel | 3 | **N/A** — known subtotal 0.0012387, coverage 2/3 (dots has no billed route) |
| 2-of-3, F3 panel | 3 | **N/A** — known subtotal 0.0001779, coverage 1/3 |
| 3-of-5 | 5 | **N/A** — known subtotal 0.0013277, coverage 3/5 |
| `reference` | 1 + one local SQL execution | 0.0000890, plus no model call and no money for the check itself |

The deterministic check is the cheapest check we have **and** the only one that caught C10. The
quorum is 3 to 5 times the price of a single call, cannot be fully priced on our panel, and still
accepted a wrong value. That is the number TD 3 has to start from.

---

## 4. The `reference` check, executed

[`scripts/age_guard_td2.py`](scripts/age_guard_td2.py) rebuilds the reference query from the
question's own parameters and runs it read-only on `data/boutique.sqlite`. The completed-age window
is written once and parameterised:

```sql
c.birth_date >  date(D, '-26 years')   AND   c.birth_date <= date(D, '-25 years')
```

with `D` the reference date of the question, or `o.date` when the question asks for the age at the
time of the order. Output in
[`outputs/routing/age-guard-20-questions.txt`](outputs/routing/age-guard-20-questions.txt):

```
case       guard  reference ref ok      2-of-3     3-of-5 verdict of the check
C10       558980     558980 yes         119410     119410 2-of-3 REJECTED (-439570 cents); 3-of-5 REJECTED (-439570 cents)
C15       168680     168680 yes              0            2-of-3 REJECTED (-168680 cents)
...
The check reproduces the reference on 20/20 questions, so a rejection above is a rejection of the
vote, not of the check.
```

The check agrees with `reference-td1.csv` on all twenty questions and rejects exactly the two values
a vote would have accepted. It is independent of the models in a way a different panel is not: it
shares no clause with any model answer. It is still not a proof of correctness — it inherits
whatever our reference inherits — but `check_references.py` in TD 1 recomputed those same twenty
amounts in pure Python without SQL, so the reference is itself double-sourced.

## 5. The simulator, before and after

**Before** — [`scripts/atelier-routage.py`](scripts/atelier-routage.py), the unchanged kit, output in
[`outputs/routing/routage-before.txt`](outputs/routing/routage-before.txt):

```
simple               run      small-free            cash=0     eligible included capacity
complex              run      senior-subscription   cash=0     eligible included capacity
deferrable           defer    senior-subscription   cash=0     recheck availability at wake-up
urgent               run      senior-api            cash=0.3   available route within the authorised budget
budget exhausted     abstain  None                  cash=0     no eligible resource within deadline and budget
high impact          run      senior-subscription   cash=0     eligible included capacity
unknown capability   abstain  None                  cash=0     no eligible resource within deadline and budget
```

**After** — [`scripts/atelier-routage-td2.py`](scripts/atelier-routage-td2.py), full output in
[`outputs/routing/routage-after.txt`](outputs/routing/routage-after.txt) and
[`routage-after.jsonl`](outputs/routing/routage-after.jsonl). What changed in the code:

- `RESOURCES` carries our five TD 1 models with their **measured per-family results**, plus two
  escalation routes of the portfolio: a billed route of the *exact same model* as our best measured
  one (so the TD 1 cells transfer — a shared family name does not establish model identity) and an
  included subscription route that was never measured.
- `choose` derives the check from the family **and** the use, tightens it when the model that answers
  is not 100 % on the family, refuses a vote on F2b, and replaces an impossible quorum with the
  deterministic check instead of a thinner vote.
- Every decision names the TD 1 cells behind it, the number of calls the check costs, and the
  API-equivalent price with its coverage.

The kit's seven scenarios still run (difficulty 1/2/3 → F1/F2/F4, `high_impact` → payout), so the two
outputs read side by side:

| Scenario | Kit, before | Our rule, after | Why it differs |
|---|---|---|---|
| simple (F1, dashboard) | run `small-free` | run `gpt-oss-20b`, check `none`, 1 call, 0.0000890 | same decision; the reason now cites 6/6 on C01,C04,C05,C06,C07,C20 and the price that made it the cheapest |
| complex (F4, dashboard) | run `senior-subscription`, 1 call | run `gpt-oss-20b` inside a **3-of-5 quorum**, 5 calls, cash 0 | the kit buys capability with a bigger model; we have no bigger measured model, so we buy reliability with a free quorum (F4 pooled 17/25) |
| deferrable (F4, Groq routes rate-limited) | **defer** 60 min | **run** cohere under the `reference` check | there is nothing to wait for: the two OpenRouter free routes are still up. With fewer than k = 3 panel members the rule replaces the vote with the deterministic check |
| urgent (F4, cannot wait, 5 min) | run `senior-api`, **cash 0.30** | run cohere under the `reference` check, **cash 0** | the check is a local SQL execution: it fits in five minutes and costs nothing, so no paid route is needed |
| budget exhausted (F4, budget 0, free routes gone, no refill) | **abstain** | run `codex:gpt-5.6-luna`, allocation 0.0000211, `reference` | a zero budget forbids new money, not capacity already paid for. The subscription has no TD 1 cell, so it is admissible *only* because the check is deterministic |
| high impact (F4, payout) | run `senior-subscription`, "source verification and human review" | run `gpt-oss-20b`, `reference` + human review, cash 0 | same intent, but the check is a named parameterised query on the database instead of a generic verification |
| unknown capability (difficulty 4) | abstain | abstain — "family not in the rule: the twenty TD 1 questions measure no cell for it" | same decision; the reason now says what is missing |

Then sixteen scenarios of our own, one per family and per cost of error, plus availability, deferral,
money and abstention. Three of them answer the priority question of section 6:

```
F2b included before defer            run     codex:gpt-5.6-luna  reference  priority=included_before_defer
F2b defer before included (reversal) defer   groq:openai/gpt-oss-20b (wake in 1 min)  priority=defer_before_included
F2b included before defer, payout    run     codex:gpt-5.6-luna  reference  priority=included_before_defer
```

## 6. Why `choose` prefers available included capacity to deferring, and when to reverse it

In the supplied `choose` the branches are evaluated in order: `included` → `waiting` → `paid` →
abstain, each with an early `return`. A subscription resource with `cash == 0` and `allocation > 0`
satisfies the `included` test (`r["available"] and r["cash"] == 0`), so the function returns on the
**first** branch and the `waiting` branch is never evaluated — even when an exhausted free resource
(`cash == 0`, `allocation == 0`) would refill before `deadline_minutes`. That order is right for
three reasons:

1. **`cash == 0` means no new money.** The subscription fee is already committed; `allocation` is an
   accounting share of it (the cost method's third quantity), not a marginal expense. Running now is
   free at the margin, so there is no saving to buy by waiting.
2. **Deferring costs something certain to buy something uncertain.** It costs `wake_in_minutes` of
   latency, and the docstring is explicit: *at wake-up, availability must be measured again; reaching
   a reset time does not prove that capacity is available*. A certain free answer now dominates a
   hypothetical free answer later.
3. **Free capacity still wins inside the branch.**
   `min(included, key=lambda r: (r["allocation"], r["level"], r["id"]))` orders by allocation first,
   so a genuinely free resource (`allocation == 0`) is taken before the subscription. The effective
   priority is: free and available → subscription available → defer for a free refill → paid →
   abstain. The subscription is only reached when no free route is up.

**The operational condition that reverses it:** when the included allocation stops being a sunk cost
and becomes a *rationed shared capacity whose consumption has an opportunity cost*. Concretely, all
of the following at once:

- the remaining monthly envelope, minus the share reserved for customer-facing and payout traffic, is
  smaller than the high-impact demand forecast before the next refill — so one dashboard call now is
  one payout call that will have to be paid for, or abstained on, later;
- the request is low-stakes (internal dashboard) and can wait;
- the free route's refill fits inside the deadline **with a margin** to re-measure availability and
  pay for one retry. Our TD 1 evidence for the horizon: the six HTTP 429 were per-minute limits
  (TPM 8000 on C19, OTPM 1000 on C16–C20) and cleared within a minute, so a one-minute refill with a
  five-minute margin is realistic. What we cannot claim is that the refill is guaranteed, which is
  exactly why the wake-up re-measures.

Implemented as the `defer_before_included` branch, guarded by
`allocation_remaining - allocation < reserve_high_impact`, and demonstrated by the three scenarios
above: with room left in the envelope the rule runs the subscription immediately; with the envelope
down to its reserve it defers the dashboard question for a one-minute refill; and it **never**
reverses for a payout, where an allocation share of 0.0000211 USD is worth nothing against a late or
wrong amount.

## 7. Limitations

- Twenty questions, one run per cell at temperature 0. The rates are a **hypothesis for this batch**:
  not a general error rate, not a permanent ranking, not a bound on quorum error. F2b rests on a
  single cell (C10) and F4 on five.
- `gpt-oss-120b` and `gpt-oss-20b` are the same model family. Our F2 and F2b fallbacks lean on that
  family, so a shared weakness would hit the first call and its fallback together. This is a known,
  unmitigated weakness of the rule: the portfolio offers no second measured family that is 4/4 on F2
  other than qwen, which is about ten times the price and carries five of our six rate-limit errors.
- The levels, availabilities and reset times in the simulator are **supplied by a scenario**, not
  measured from a provider. The prices are a computation under the assumptions stated in section 3,
  not a bill. Two of five models have no priceable billed route, so no quorum cost is complete.
- `codex:gpt-5.6-luna` has never been measured on these questions; the rule only admits it behind the
  deterministic check, and its accuracy there is unknown — it affects the retry rate, which we cannot
  quantify.
- The `reference` check assumes the question's parameters are parsed correctly and that a reference
  query exists for its family. A new family arrives with no measured rate and no golden query: the
  rule abstains, as the `unknown capability` scenario shows.

## 8. Questions where no free model is enough on its own (input for TD 3)

Per the plenary instruction: on **C10** (F2b) no admissible panel of distinct model families returns
the reference, and on **C15** and **C17** (F4) every configuration either abstains or is wrong. These
three questions are where the price of checking is actually set — and the answer our traces give is
that the cheapest adequate check is not a bigger quorum but a deterministic recomputation.
