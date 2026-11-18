# TD 2 report — the quorum, then the routing rule

Session: 18 November 2026, 13:30 to 18:00. Kit: pack `2026-11-18-students-5`.
Sub-group 3 (DIA 1).

**No new provider call was made for TD 2.** Every figure in this report is derived from the 100
real TD 1 cells committed in [`../td1/`](../td1/) (`nature = real`). Where a supplied or
constructed example is used, it is labelled as such.

**State of the three steps:**

| Step | Owner | Status | Where |
|---|---|---|---|
| Step 1 — the k-of-n vote (`vote_k_sur_n`, 2-of-3 versus 3-of-5 on twenty questions) | Pair A | **Complete** | section 1 |
| Step 2 — the wrong consensus, its SQL cause and the delta query | Pair B | **Complete** | section 2 |
| Step 3 — the routing rule, the simulator, the priority analysis | **Pair C (VERDES Adrian)** | **Complete** | section 3 |

## 0. What is in this folder

| File | What it is |
|---|---|
| [`scripts/family_rates_td2.py`](scripts/family_rates_td2.py) | Derives the exact TD 1 rate of every question family, and what a 2-of-3 panel, a 3-of-5 quorum and our own panels would have returned. Writes the two CSV files below. |
| [`analysis/csv/family-rates-td1.csv`](analysis/csv/family-rates-td1.csv) | `correct / cases` per family and per model, with every failing cell named |
| [`analysis/csv/quorum-by-family-td1.csv`](analysis/csv/quorum-by-family-td1.csv) | One row per question: decision, value, votes and agreement with the reference, for the three configurations |
| [`scripts/atelier-routage.py`](scripts/atelier-routage.py) | The kit's simulator, unchanged, kept so the "before" output can be reproduced |
| [`scripts/atelier-routage-td2.py`](scripts/atelier-routage-td2.py) | The simulator adapted to our rule: our models, our per-family eligibility, our checks, TD 1 cells in every reason |
| [`scripts/age_guard_td2.py`](scripts/age_guard_td2.py) | The deterministic check the rule calls `reference`, executed on `data/boutique.sqlite` |
| [`B/`](B/) | Step 2 (pair B): write-up [`B/README.md`](B/README.md), scripts, delta SQL and output |
| [`outputs/routing/`](outputs/routing/) | Saved outputs: before, after, the rule table, the family rates, the check on the twenty questions |

Reproduce everything from the repository root:

```powershell
python td2/scripts/family_rates_td2.py --print
python td2/scripts/atelier-routage.py                      # before
python td2/scripts/atelier-routage-td2.py --table          # after
python td2/scripts/atelier-routage-td2.py --check-rates    # embedded rates vs the CSV
python td2/scripts/age_guard_td2.py <student-kit-dir>      # the reference check on C01..C20
python td2/B/scripts/pair_b_wrong_consensus.py --db <student-kit-dir>/data/boutique.sqlite   # step 2
```

---

## 1. Step 1 — the k-of-n vote (pair A)

Full write-up, code, tests and outputs: [`A/README.md`](A/README.md). Reviews written by pair A: [`A/groupe-B.md`](A/groupe-B.md) (pair B) and [`A/groupe-C.md`](A/groupe-C.md) (pair C).

`Orchestrateur.vote_k_sur_n` is completed in [`A/scripts/skeleton-multi-llm-en.py`](A/scripts/skeleton-multi-llm-en.py) (strict majority, abstention, unavailable members stay in n, duplicates refused). It was written with Claude's help and read, run and tested by pair A. Results on the twenty real TD 1 questions, from [`A/analysis/csv/step1-table.csv`](A/analysis/csv/step1-table.csv):

| Quorum | Consensus | Correct | Wrong | Abstentions |
|---|---|---|---|---|
| Fixed panel, 2-of-3 | 18 | 16 | **2** (C10, C15) | 2 (C17, C19) |
| All five models, 3-of-5 | 17 | 16 | **1** (C10) | 3 (C02, C15, C17) |

Three decisions change between the two quorums: C02 (correct → abstention), C15 (wrong → abstention), C19 (abstention → correct). The tables of section 3.2 (pair C's independent implementation) and of `A/README.md` agree cell by cell: 0 differences.

## 2. Step 2 — the wrong consensus (pair B)

Full write-up, SQL, code and outputs: [`B/README.md`](B/README.md). Reviews written by pair B: [`B/groupe-A.md`](B/groupe-A.md) (pair A) and [`B/groupe-C.md`](B/groupe-C.md) (pair C).

Four shared wrong values in the 100 real TD 1 cells (votes cross-checked with pair A's `vote_k_sur_n`: 8/8 identical):

| Case | Shared wrong value | Models agreeing | Reference | 2-of-3 panel | 3-of-5 quorum |
|---|---|---|---|---|---|
| C02 | 0 | 20B, Dots | 590320 | 590320, correct | abstain |
| C08 | 0 | Cohere, Dots | 605580 | 605580, correct | 605580, correct |
| **C10** | **119410** | **Cohere, Qwen, Dots** | **558980** | **119410, WRONG** | **119410, WRONG** |
| C15 | 0 | Cohere, Qwen | 168680 | 0, WRONG | abstain |

**C10 (age at the time of the order)** is the only case where the wrong value wins both quorums. Root cause: completed age 25 at the order date covers (a) year difference 25 with birthday reached and (b) year difference 26 with birthday not yet reached; Cohere and Dots test only (a), Qwen adds a branch with `= 24` instead of `= 26` (age 23, 0 rows). The delta query on `data/boutique.sqlite` ([`B/scripts/delta_c10.sql`](B/scripts/delta_c10.sql)) returns 4 customers (C004, C005, C007, C022), 59 order lines, **439570 cents = 558980 − 119410**, with 0 rows wrongly added; an independent Python age recomputation gives the same figures.

Consequence: a quorum only protects against independent errors; for the age families a deterministic check is required (section 3.4).

---

# 3. Step 3 — the routing rule (pair C)

## 3.1 The exact TD 1 rate of each family

Families are the question types of `questions-td1-en.md`. Rates are regenerated by
`family_rates_td2.py` from the 100-cell comparison table; `--check-rates` verifies that the numbers
embedded in the simulator still match the CSV.

| Family | TD 1 cells | gpt-oss-120b | gpt-oss-20b | cohere north-mini | qwen3.8-27b | dots-3-note | Pooled |
|---|---|---|---|---|---|---|---|
| **F1** period | C01, C04, C05, C06, C07, C20 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | **30/30** |
| **F2** completed age on a reference date | C02, C08, C09, C11 | **4/4** | 2/4 | 0/4 | **4/4** | 2/4 | **12/20** |
| **F2b** age at the time of the order | C10 | 1/1 | 1/1 | 0/1 | 0/1 | 0/1 | **2/5** |
| **F3** product list | C03, C12, C13, C14 | 4/4 | 4/4 | 4/4 | 3/4 | 4/4 | **19/20** |
| **F4** combined filters | C15, C16, C17, C18, C19 | 4/5 | **5/5** | 3/5 | 2/5 | 3/5 | **17/25** |

Failing cells, from the CSV:

- F2 — 20b: C02 returns 0 (window of age 0), C11 returns 322160 (ages 20 to 24). cohere: C02
  `sql_invalid`, C08/C09/C11 return 0. dots: C02 and C08 return 0.
- F2b — cohere, qwen and dots all return 119410 on C10.
- F3 — qwen: C12 `sql_rejected`, an unclosed ```` ```sql ```` fence. A format failure, but a lost
  cell all the same.
- F4 — 120b: C19 returns 0. cohere: C15 returns 0, C17 returns 197080. qwen: C15 returns 0, C17
  returns 248490, C19 returns 83580. dots: C15 returns 138920, C17 `sql_invalid`.

**The one fact the whole rule rests on:** 19 of the 20 failed cells carry an age clause. The period
and product clauses cost us nothing in this batch (F1 30/30, F3 19/20, the single F3 loss being a
formatting accident). So the rule is cheap where there is no age, and deterministic where there is.

## 3.2 What a vote would have returned (cross-check for pair A)

From [`analysis/csv/quorum-by-family-td1.csv`](analysis/csv/quorum-by-family-td1.csv). Fixed panel =
`gpt-oss-120b`, `cohere/north-mini-code:free`, `qwen3.8-27b` with k = 2 (the panel of
`atelier-vote.py`). Quorum = the five TD 1 models with k = 3. A cell with no value
(`sql_invalid`, `sql_rejected`) stays in n and casts no vote.

| Question | Reference | Fixed 2-of-3 | 3-of-5 | Our rule panel |
|---|---|---|---|---|
| C01 F1 | 792800 | 792800 (3 votes) ✔ | 792800 (5) ✔ | 792800 (3) ✔ |
| C02 F2 | 590320 | 590320 (2) ✔ | **abstain** (2-2 tie with 0) | 590320 (2) ✔ |
| C03 F3 | 936350 | 936350 (3) ✔ | 936350 (5) ✔ | 936350 (3) ✔ |
| C04 F1 | 2826250 | 2826250 (3) ✔ | 2826250 (5) ✔ | 2826250 (3) ✔ |
| C05 F1 | 38480 | 38480 (3) ✔ | 38480 (5) ✔ | 38480 (3) ✔ |
| C06 F1 | 0 | 0 (3) ✔ | 0 (5) ✔ | 0 (3) ✔ |
| C07 F1 | 13970 | 13970 (3) ✔ | 13970 (5) ✔ | 13970 (3) ✔ |
| C08 F2 | 605580 | 605580 (2) ✔ | 605580 (3) ✔ | 605580 (2) ✔ |
| C09 F2 | 487980 | 487980 (2) ✔ | 487980 (4) ✔ | 487980 (3) ✔ |
| **C10 F2b** | **558980** | **119410 (2) ✘** | **119410 (3) ✘** | no panel admissible → abstain |
| C11 F2 | 446690 | 446690 (2) ✔ | 446690 (3) ✔ | 446690 (3) ✔ |
| C12 F3 | 1666490 | 1666490 (2) ✔ | 1666490 (4) ✔ | 1666490 (3) ✔ |
| C13 F3 | 107740 | 107740 (3) ✔ | 107740 (5) ✔ | 107740 (3) ✔ |
| C14 F3 | 0 | 0 (3) ✔ | 0 (5) ✔ | 0 (3) ✔ |
| **C15 F4** | **168680** | **0 (2) ✘** | abstain (2) | abstain (2) |
| C16 F4 | 376740 | 376740 (3) ✔ | 376740 (5) ✔ | 376740 (5) ✔ |
| C17 F4 | 258180 | abstain (1) | abstain (2) | abstain (2) |
| C18 F4 | 62480 | 62480 (3) ✔ | 62480 (5) ✔ | 62480 (5) ✔ |
| C19 F4 | 1990 | abstain (1) | 1990 (3) ✔ | 1990 (3) ✔ |
| C20 F1 | 1106090 | 1106090 (3) ✔ | 1106090 (5) ✔ | 1106090 (3) ✔ |

Totals, reference / wrong / abstention:

| Family | Fixed 2-of-3 | 3-of-5 | Our rule panel |
|---|---|---|---|
| F1 (6) | 6 / 0 / 0 | 6 / 0 / 0 | 6 / 0 / 0 |
| F2 (4) | 4 / 0 / 0 | 3 / 0 / 1 | 4 / 0 / 0 |
| F2b (1) | 0 / **1** / 0 | 0 / **1** / 0 | 0 / 0 / 1 |
| F3 (4) | 4 / 0 / 0 | 4 / 0 / 0 | 4 / 0 / 0 |
| F4 (5) | 2 / **1** / 2 | 3 / 0 / 2 | 3 / 0 / 2 |
| **All 20** | 16 / **2** / 2 | 16 / **1** / 3 | **17 / 0 / 3** |

Three readings drive the rule:

1. **A larger quorum is not uniformly safer.** Going from 2-of-3 to 3-of-5 removes the wrong
   consensus on C15 (0 instead of 168680, because cohere and qwen agree on 0 in the fixed panel) but
   turns a correct answer into an abstention on C02 (590320 gets 2 votes, 0 gets 2 votes from 20b and
   dots, and cohere casts no vote at all because its SQL is invalid). It changes which error you
   make, not whether you make one.
2. **On F2b no quorum works.** Both configurations return 119410. The only 2-of-3 panel that returns
   the reference is `gpt-oss-120b + gpt-oss-20b + anything`, i.e. two members of the *same* model
   family — the configuration lecture 2 tells us not to buy safety with, because models trained on
   close data are wrong together. C10 is that lecture, measured.
3. **Panels built per family are strictly better than one fixed panel.** Choosing panel members from
   the models TD 1 shows correct on that family, keeping three distinct model families and two
   providers, gives 17 / 0 / 3 over the twenty questions: no wrong value anywhere, against 2 for the
   fixed panel and 1 for the 3-of-5 quorum.

---

## 3.3 The rule (one page)

**Principle.** The question's family sets who is called; the cost of an error sets what checks the
answer. An age clause is the only thing that failed in our batch, so an age clause is the only thing
that pays for a deterministic check. `none` is never used where a model erred on the family, nor on
a figure shown to a customer, nor on an amount paid out.

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

At request time every free route costs 0, so "the cheapest one" is decided by the price the
portfolio *does* document for the exact same model (what this configuration would cost a company),
then by the rate-limit friction measured in TD 1 (qwen: 5 × HTTP 429 on C16–C20, OTPM 1000; 20b:
1 × HTTP 429 on C19, TPM 8000), then by median latency (Groq 0.4–0.8 s, OpenRouter free 2.4–2.8 s).
A route whose billed equivalent is N/A cannot be called the cheapest, so it ranks last among equals.

### The rule, family by family

| Family | TD 1 cells and rate | First call (cheapest correct on the family) | Internal dashboard | Figure shown to the customer | Amount paid out | If the first model is unavailable |
|---|---|---|---|---|---|---|
| **F1** period | C01,C04,C05,C06,C07,C20 — every model 6/6, pooled 30/30 | `gpt-oss-20b` (free, 0.0000890, cheapest documented equivalent, 6/6) | **none** — admissible: 6/6 on the family *and* low stakes | **2-of-3** on {120b, qwen, dots} — 6/6 on our traces | **reference** + human review | 120b → qwen → cohere → dots (all 6/6) → billed 120b (0.0001779) → defer → abstain |
| **F2** completed age at a date | C02,C08,C09,C11 — 120b 4/4, qwen 4/4, 20b 2/4, dots 2/4, cohere 0/4, pooled 12/20 | `gpt-oss-120b` (free, 4/4; cheaper than qwen's 0.0010608 and 5 × 429) | **none, but only with 120b or qwen.** Any other model erred on C02, C08, C09 or C11 → the check tightens to 2-of-3 | **2-of-3** on {120b, qwen, dots} — 4/4 on our traces, where the 3-of-5 abstains on C02 | **reference** + human review | qwen (4/4) → billed 120b → defer for the Groq refill → abstain. **Never** 20b, cohere or dots alone, and **never** a vote among them: on C02 20b and dots both answer 0 |
| **F2b** age at the time of the order | C10 — 120b 1/1, 20b 1/1, cohere/qwen/dots 0/1, pooled 2/5 | `gpt-oss-20b` (free, cheapest of the two correct) behind the check | **reference** | **reference** | **reference** + human review | 120b → billed 120b → subscription behind the same check → defer → abstain |
| **F3** product list | C03,C12,C13,C14 — 120b, 20b, cohere, dots 4/4, qwen 3/4, pooled 19/20 | `gpt-oss-20b` (free, 4/4, cheapest) | **none** — 4/4 on the family and low stakes | **2-of-3** on {120b, cohere, dots} — 4/4 on our traces | **reference** + human review | 120b → cohere → dots → billed 120b → abstain. qwen last: C12 `sql_rejected` |
| **F4** combined filters | C15–C19 — 20b 5/5, 120b 4/5, cohere 3/5, dots 3/5, qwen 2/5, pooled 17/25 | `gpt-oss-20b` (free, 5/5), inside the quorum | **3-of-5** | **3-of-5** | **reference** + human review | defer for a refill → billed 120b → abstain. A quorum that cannot reach k is replaced by the reference check, not by a thinner vote |

**Why F2b takes no vote at any stake.** On C10 the fixed 2-of-3 panel returns 119410 with 2 votes of
3, and the 3-of-5 quorum returns 119410 with 3 votes of 5 — both wrong by 439570 cents. A check that
is a second opinion cannot catch an error the panel shares. The check must recompute the answer from
the question, which is what section 3.4 does.

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
  admissible, on every family including the ones where every model scored 100 %: F1 is 30/30 in a
  batch of six questions, which bounds nothing about the next question.

**What the checking costs** (API equivalent per request, same envelope):

| Check | Model calls | Cost |
|---|---:|---|
| `none` | 1 | 0.0000890 (20b) or 0.0001779 (120b) |
| 2-of-3, F1/F2 panel | 3 | **N/A** — known subtotal 0.0012387, coverage 2/3 (dots has no billed route) |
| 2-of-3, F3 panel | 3 | **N/A** — known subtotal 0.0001779, coverage 1/3 |
| 3-of-5 | 5 | **N/A** — known subtotal 0.0013277, coverage 3/5 |
| `reference` | 1 + one local SQL execution | 0.0000890, plus no model and no money for the check itself |

The deterministic check is the cheapest check we have *and* the only one that caught C10. The
quorum is 3 to 5 times the price of a single call, cannot be fully priced on our panel, and still
accepted a wrong value. That is the number TD 3 has to start from.

---

## 3.4 The `reference` check, executed

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

## 3.5 The simulator, before and after

Before — [`scripts/atelier-routage.py`](scripts/atelier-routage.py), unchanged kit, output in
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

After — [`scripts/atelier-routage-td2.py`](scripts/atelier-routage-td2.py), full output in
[`outputs/routing/routage-after.txt`](outputs/routing/routage-after.txt) and
[`routage-after.jsonl`](outputs/routing/routage-after.jsonl). What changed in the code:

- `RESOURCES` carries our five TD 1 models with their **measured per-family results**, plus two
  escalation routes of the portfolio. Eligibility is per family, not one `level` number: TD 1 shows
  `gpt-oss-20b` at 5/5 on F4 but 2/4 on F2, so a single capability scalar cannot carry the rule.
- `choose` derives the check from the family **and** the use, tightens it when the model that
  answers is not 100 % on the family, and refuses a vote on F2b.
- Every decision names the TD 1 cells behind it, the number of calls the check costs, and the
  API-equivalent price with its coverage.

The kit's seven scenarios still run (difficulty 1/2/3 → F1/F2/F4, `high_impact` → payout), so the
two outputs read side by side:

| Scenario | Kit, before | Our rule, after | Why it differs |
|---|---|---|---|
| simple (F1, dashboard) | run `small-free` | run `gpt-oss-20b`, check `none`, 1 call, 0.0000890 | same decision; the reason now cites 6/6 on C01,C04,C05,C06,C07,C20 and the price that made it the cheapest |
| complex (F4, dashboard) | run `senior-subscription`, 1 call | run `gpt-oss-20b` inside a **3-of-5 quorum**, 5 calls, cash 0 | the kit buys capability with a bigger model; we have no bigger measured model, so we buy reliability with a free quorum (F4 pooled 17/25) |
| deferrable (F4, Groq routes rate-limited) | **defer** 60 min | **run** cohere under the `reference` check | there is nothing to wait for: the two OpenRouter free routes are still up. With fewer than k = 3 panel members the rule replaces the vote with the deterministic check, not with a thinner vote |
| urgent (F4, cannot wait, 5 min) | run `senior-api`, **cash 0.30** | run cohere under the `reference` check, **cash 0** | the check is a local SQL execution: it fits in five minutes and costs nothing, so no paid route is needed |
| budget exhausted (F4, budget 0, free routes gone, no refill) | **abstain** | run `codex:gpt-5.6-luna`, allocation 0.0000211, `reference` | a zero budget forbids new money, not capacity already paid for. The subscription has no TD 1 cell, so it is admissible *only* because the check is deterministic |
| high impact (F4, payout) | run `senior-subscription`, "source verification and human review" | run `gpt-oss-20b`, `reference` + human review, cash 0 | same intent, but the check is a named parameterised query on the database instead of a generic verification |
| unknown capability (difficulty 4) | abstain | abstain — "family not in the rule: the twenty TD 1 questions measure no cell for it" | same decision; the reason now says what is missing |

Then our own scenarios, one per family and per cost of error, plus availability, deferral, money and
abstention. Three of them answer the priority question of section 3.6:

```
F2b included before defer            run     codex:gpt-5.6-luna  reference  priority=included_before_defer
F2b defer before included (reversal) defer   groq:openai/gpt-oss-20b (wake in 1 min)  priority=defer_before_included
F2b included before defer, payout    run     codex:gpt-5.6-luna  reference  priority=included_before_defer
```

## 3.6 Why `choose` prefers available included capacity to deferring, and when to reverse it

In the supplied `choose` the branches are evaluated in order: `included` → `waiting` → `paid` →
abstain, each with an early `return`. A subscription resource with `cash == 0` and
`allocation > 0` satisfies the `included` test (`r["available"] and r["cash"] == 0`), so the
function returns on the **first** branch and the `waiting` branch is never evaluated — even when an
exhausted free resource (`cash == 0`, `allocation == 0`) would refill before
`deadline_minutes`. That order is right for three reasons:

1. **`cash == 0` means no new money.** The subscription fee is already committed; `allocation` is an
   accounting share of it (methode-cout's third quantity), not a marginal expense. Running now is
   free at the margin, so there is no saving to buy by waiting.
2. **Deferring costs something certain to buy something uncertain.** It costs `wake_in_minutes` of
   latency, and the docstring is explicit: *at wake-up, availability must be measured again;
   reaching a reset time does not prove that capacity is available*. A certain free answer now
   dominates a hypothetical free answer later.
3. **Free capacity still wins inside the branch.** `min(included, key=lambda r: (r["allocation"],
   r["level"], r["id"]))` orders by allocation first, so a genuinely free resource
   (`allocation == 0`) is taken before the subscription. The effective priority is: free and
   available → subscription available → defer for a free refill → paid → abstain. The subscription
   is only reached when no free route is up.

**The operational condition that reverses it:** when the included allocation stops being a sunk cost
and becomes a *rationed shared capacity whose consumption has an opportunity cost*. Concretely, all
of the following at once:

- the remaining monthly envelope, minus the share reserved for customer-facing and payout traffic,
  is smaller than the high-impact demand forecast before the next refill — so one dashboard call now
  is one payout call that will have to be paid for, or abstained on, later;
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

## 3.7 Limitations of this rule

- Twenty questions, one run per cell at temperature 0. The rates are a **hypothesis for this batch**:
  not a general error rate, not a permanent ranking, not a bound on quorum error. F2b rests on a
  single cell (C10) and F4 on five.
- `gpt-oss-120b` and `gpt-oss-20b` are the same model family. Our F2 and F2b fallbacks lean on that
  family, so a shared weakness would hit the first call and its fallback together. This is a known,
  unmitigated weakness of the rule: the portfolio offers no second measured family that is 4/4 on F2
  other than qwen, which is 10 × the price and carries 5 of our 6 rate-limit errors.
- The levels, availabilities and reset times in the simulator are **supplied by a scenario**, not
  measured from a provider. The prices are a computation under the assumptions stated in 3.3, not a
  bill. Two of five models have no priceable billed route, so no quorum cost is complete.
- `codex:gpt-5.6-luna` has never been measured on these questions; the rule only admits it behind
  the deterministic check, and its accuracy there is unknown — it affects the retry rate, which we
  cannot quantify.
- The `reference` check assumes the question's parameters are parsed correctly and that a reference
  query exists for its family. A new family would arrive with no measured rate and no golden query:
  the rule abstains, as the `unknown capability` scenario shows.

## 3.8 Questions where no free model is enough on its own (input for TD 3)

Per the plenary instruction: on **C10** (F2b) no admissible panel of distinct model families returns
the reference, and on **C15 and C17** (F4) every configuration either abstains or is wrong. These
three questions are where the price of checking is actually set — and the answer our traces give is
that the cheapest adequate check is not a bigger quorum but a deterministic recomputation.

---

## 4. Contributions

| Member | Pair | Work in TD 2 |
|---|---|---|
| VERDES Adrian | **C** | Step 3 in full: per-family TD 1 rates and the script that derives them, quorum cross-check, the one-page rule, the adapted simulator, the deterministic `reference` check, the priority analysis, this report's section 3 and the repository restructuring |
| PERKINS Luca, NORAT Faizan | A | Step 1: `vote_k_sur_n`, the four synthetic examples, the twenty-question 2-of-3 versus 3-of-5 table |
| SAAID Myriam, DE GENTILE Océane | B | Step 2: scan of the 100 cells, quorum verdicts, C10 SQL root cause, delta query and independent check on `data/boutique.sqlite`, DEMO-VOTE, cross-check with pair A's vote, this report's section 2 |

