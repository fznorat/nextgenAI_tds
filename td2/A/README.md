# TD 2 — Pair A: Step 1, the k-of-n vote

Session: 18 November 2026. Sub-group 3 (DIA 1). Author: PERKINS Luca NORAT Faizan

**No new provider call was made.** All figures come from the 100 real TD 1 cells in [`../../td1/data/traces/traces-td1.csv`](../../td1/data/traces/traces-td1.csv).


**Nature of the data:** real TD 1 traces (`nature = real`, final attempt per model and question), no new provider call. Model letters A–E are the TD 1 models, not the session pairs: A = `openai/gpt-oss-120b`, B = `openai/gpt-oss-20b`, C = `cohere/north-mini-code:free`, D = `qwen/qwen3.8-27b`, E = `dots-studio/dots-3-note-preview:free`.

**Method** ([`scripts/skeleton-multi-llm-en.py`](scripts/skeleton-multi-llm-en.py), only `Orchestrateur.vote_k_sur_n` changed):

1. n is the number of proposals. k must satisfy `n // 2 < k <= n`, otherwise `ValueError`. A strict majority guarantees two different values cannot both reach k.
2. Two proposals with the same (provider, model) raise `ValueError`: a duplicate is not a second vote.
3. Only `executed` proposals with `value is not None` vote. An error (`sql_invalid`, `sql_rejected`, HTTP failure) stays in n and casts no vote. `0` is a value.
4. If a value reaches k: `consensus = True`, the value, its votes and the models. Otherwise `consensus = False`, `value = None`, the largest vote count, an empty model list. It never invents a value, and it never sees the reference (the comparison is made afterwards).

**Tests (no network).** [`scripts/test_vote.py`](scripts/test_vote.py) runs 15 checks and prints `all tests passed`: k = 1 of 3, k = 4 of 3 and k = 2 of 4 refused; empty panel refused; a duplicate (provider, model) refused, including one in error, while the same model name at another provider is allowed; 2 of 3 agreeing gives consensus; `0` is a value; three different values abstain with `value = None`, 1 vote and no models; 3-of-5 with a 2–2 split plus one unavailable member abstains with 2 votes; nobody voted abstains with 0 votes; `[0, 0, 100]` keeps 0 because the vote never sees the reference. The four synthetic examples of `atelier-vote.py` also pass (`nature = simulation`).

**Reproduce** from the repository root:

```powershell
python td2/A/scripts/test_vote.py
python td2/A/scripts/atelier-vote.py
python td2/A/scripts/atelier-vote.py --traces td1/data/traces/traces-td1.csv --case C10
python td2/A/scripts/step1_table.py --traces td1/data/traces/traces-td1.csv --reference td1/data/references/reference-td1.csv --skeleton td2/A/scripts/skeleton-multi-llm-en.py --out td2/A/analysis/csv/step1-table.csv
```

Files: [`scripts/step1_table.py`](scripts/step1_table.py), [`analysis/csv/step1-table.csv`](analysis/csv/step1-table.csv), [`outputs/vote/votes-20-questions-2of3.jsonl`](outputs/vote/votes-20-questions-2of3.jsonl) (one `atelier-vote.py` line per question, fixed panel). `step1_table.py` loads the completed skeleton and uses the same `vote_k_sur_n` for both quorums.

**The twenty decisions.** 2-of-3 = fixed panel A, C, D with k = 2. 3-of-5 = A–E with k = 3. “–” = abstention. `step1-table.csv` also has the columns `2of3_voters` and `3of5_voters` (members that returned a value, out of n).

**Why this panel.** A, C, D is the fixed panel of `atelier-vote.py` (three families, two providers), not a choice of ours. The only 2-of-3 panel that would be right on C10 contains gpt-oss-120b **and** gpt-oss-20b, two models of the same family, which lecture 2 advises against; widening to five models does not help either, because Dots shares the same mistake.

| Case | Ref | A | B | C | D | E | 2-of-3 (votes) | vs ref | 3-of-5 (votes) | vs ref |
|---|---|---|---|---|---|---|---|---|---|---|
| C01 | 792800 | 792800 | 792800 | 792800 | 792800 | 792800 | 792800 (3) | yes | 792800 (5) | yes |
| C02 | 590320 | 590320 | 0 | (sql_invalid) | 590320 | 0 | 590320 (2) | yes | abstain (2) | - |
| C03 | 936350 | 936350 | 936350 | 936350 | 936350 | 936350 | 936350 (3) | yes | 936350 (5) | yes |
| C04 | 2826250 | 2826250 | 2826250 | 2826250 | 2826250 | 2826250 | 2826250 (3) | yes | 2826250 (5) | yes |
| C05 | 38480 | 38480 | 38480 | 38480 | 38480 | 38480 | 38480 (3) | yes | 38480 (5) | yes |
| C06 | 0 | 0 | 0 | 0 | 0 | 0 | 0 (3) | yes | 0 (5) | yes |
| C07 | 13970 | 13970 | 13970 | 13970 | 13970 | 13970 | 13970 (3) | yes | 13970 (5) | yes |
| C08 | 605580 | 605580 | 605580 | 0 | 605580 | 0 | 605580 (2) | yes | 605580 (3) | yes |
| C09 | 487980 | 487980 | 487980 | 0 | 487980 | 487980 | 487980 (2) | yes | 487980 (4) | yes |
| C10 | 558980 | 558980 | 558980 | 119410 | 119410 | 119410 | 119410 (2) | NO | 119410 (3) | NO |
| C11 | 446690 | 446690 | 322160 | 0 | 446690 | 446690 | 446690 (2) | yes | 446690 (3) | yes |
| C12 | 1666490 | 1666490 | 1666490 | 1666490 | (sql_rejected) | 1666490 | 1666490 (2) | yes | 1666490 (4) | yes |
| C13 | 107740 | 107740 | 107740 | 107740 | 107740 | 107740 | 107740 (3) | yes | 107740 (5) | yes |
| C14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 (3) | yes | 0 (5) | yes |
| C15 | 168680 | 168680 | 168680 | 0 | 0 | 138920 | 0 (2) | NO | abstain (2) | - |
| C16 | 376740 | 376740 | 376740 | 376740 | 376740 | 376740 | 376740 (3) | yes | 376740 (5) | yes |
| C17 | 258180 | 258180 | 258180 | 197080 | 248490 | (sql_invalid) | abstain (1) | - | abstain (2) | - |
| C18 | 62480 | 62480 | 62480 | 62480 | 62480 | 62480 | 62480 (3) | yes | 62480 (5) | yes |
| C19 | 1990 | 0 | 1990 | 1990 | 83580 | 1990 | abstain (1) | - | 1990 (3) | yes |
| C20 | 1106090 | 1106090 | 1106090 | 1106090 | 1106090 | 1106090 | 1106090 (3) | yes | 1106090 (5) | yes |

**Totals.** 2-of-3: 18 consensus, 16 correct, **2 wrong (C10, C15)**, 2 abstentions (C17, C19). 3-of-5: 17 consensus, 16 correct, **1 wrong (C10)**, 3 abstentions (C02, C15, C17).

**The three decisions that change between the two quorums**

- **C02** (correct 590320 → abstention). A and D return 590320; C is `sql_invalid` (`syntax_error near "AS"`), which stays in n without a vote, so 2-of-3 reaches k = 2. In 3-of-5, B and E both return 0 (wrong): 2 votes for 590320 and 2 for 0, neither reaches k = 3.
- **C15** (wrong 0 → abstention). C and D both return 0 (reference 168680), so the fixed panel keeps a wrong value. A and B return 168680 (2 votes), E returns 138920 (1 vote): in 3-of-5 no value reaches 3.
- **C19** (abstention → correct 1990). Fixed panel: A returns 0 (`c.birth_date = date('2026-09-25', '-25 years')`, exact match), C returns 1990, D returns 83580, 1 vote each. B, C and E all return 1990, so 3-of-5 reaches k = 3 on the correct value.

**Decisions taken at the limit.** In 2-of-3, C02 and C12 have only 2 effective voters out of 3 (Cohere is `sql_invalid` on C02, Qwen is `sql_rejected` on C12), so one more failure (for example an HTTP 429) would have turned them into abstentions; C08, C09 and C11 pass with exactly k = 2 votes. The columns `2of3_voters` and `3of5_voters` of `step1-table.csv` show this.

**Margin changes without a change of decision.** C08: 2 → 3 votes (A, B, D; C and E return 0). C09: 2 → 4 (only C returns 0). C11: 2 → 3 (B returns 322160, C returns 0). C12: 2 → 4 (D is `sql_rejected`: `not_select`, its answer was wrapped in a ```sql fence, so it stays in n without a vote). C10: 2 → 3 votes for the same wrong value 119410 (C, D, E). C17: abstains in both, although the correct value 258180 leads in 3-of-5 — that is the cost of an abstention: no wrong answer, but no answer at all; pair C lists C17 with C10 and C15 among the questions where no free model is enough on its own (section 3.8 of pair C's report) (2-of-3: 258180, 197080, 248490; 3-of-5: 258180 has 2 votes from A and B, E is `sql_invalid`, k = 3 is not reached although the correct value leads).

**Cross-check with pair C.** Pair C implemented the same contract independently (`vote_k_of_n` in its `family_rates_td2.py`, table in its section 3.2). Compared cell by cell (decision, value and votes, for both the 2-of-3 and the 3-of-5 columns, on all twenty questions), the two tables have **0 differences**. Two independent implementations on the same 100 cells give the same decisions.

**Reading.**
- A quorum measures agreement, not correctness: on C10 three models share the same SQL mistake and the vote keeps 119410 in both configurations (cause and delta query in pair B's folder).
- A larger quorum changes which error you make: it removes the wrong consensus on C15 and turns a correct answer into an abstention on C02.
- An abstention is a cost (no answer), not an error; whether it is acceptable depends on the use (pair C's rule).
- Twenty questions support a batch-specific observation only, not a general error rate or a quorum guarantee.
