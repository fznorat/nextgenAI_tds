# TD 2 — Pair B: Step 2, the wrong consensus

Session: 18 November 2026. Sub-group 3 (DIA 1). Pair B: SAAID Myriam, DE GENTILE Océane.

**Nature of the data:** real TD 1 traces in [`../../td1/data/traces/traces-td1.csv`](../../td1/data/traces/traces-td1.csv) (`nature = real`, last attempt per model and question), no new provider call. All SQL below was executed read-only on `data/boutique.sqlite` (student kit, not committed). The only constructed material is DEMO-VOTE (section 6), labelled as such.

**Declaration:** AI assistance (Claude) was used to help write the diagnostic queries, the script and this write-up; pair B executed the queries, checked the results on `data/boutique.sqlite` and counted the votes by hand.

**Files:**

| File | What it is |
|---|---|
| [`scripts/pair_b_wrong_consensus.py`](scripts/pair_b_wrong_consensus.py) | Scan of the 100 cells, 2-of-3 and 3-of-5 votes, C10 replay, delta query, independent Python check, DEMO-VOTE, cross-check with pair A's `vote_k_sur_n` |
| [`scripts/delta_c10.sql`](scripts/delta_c10.sql) | The delta diagnostic query (rows missed by the faulty queries) |
| [`scripts/check_c10.sql`](scripts/check_c10.sql) | One-line control: reference, case (a) only, case (b) missed |
| [`outputs/wrong-consensus/pair_b_output.txt`](outputs/wrong-consensus/pair_b_output.txt) | Saved output of the script |

**Reproduce** from the repository root:

```powershell
python td2/B/scripts/pair_b_wrong_consensus.py --db <student-kit-dir>/data/boutique.sqlite
```

## 1. Shared wrong values in the 100 cells

Search: verdict `incorrect`, same question, identical value, at least two distinct models among the five (20B and Dots included). Only `correct`/`incorrect` cells with a value vote; `sql_invalid` stays in n without a vote.

| Case | Shared wrong value | Models agreeing | Reference | 2-of-3 panel (120B, Cohere, Qwen) | 3-of-5 quorum (all five) |
|---|---|---|---|---|---|
| C02 | 0 | 20B, Dots | 590320 | 590320 (2 votes: 120B, Qwen), correct; Cohere `sql_invalid` stays in n | **abstain**: 590320 ×2, 0 ×2, Cohere no vote |
| C08 | 0 | Cohere, Dots | 605580 | 605580 (2 votes), correct | 605580 (3 votes: 120B, 20B, Qwen), correct |
| **C10** | **119410** | **Cohere, Qwen, Dots** | **558980** | **119410 (2 votes), WRONG CONSENSUS** | **119410 (3 votes), WRONG CONSENSUS** |
| C15 | 0 | Cohere, Qwen | 168680 | **0 (2 votes), WRONG CONSENSUS** | abstain: 168680 ×2, 0 ×2, 138920 ×1 |

Votes counted by hand, then recomputed with pair A's `vote_k_sur_n` ([`../A/scripts/skeleton-multi-llm-en.py`](../A/scripts/skeleton-multi-llm-en.py)): **8 decisions out of 8 identical, 0 differences**. `atelier-vote.py --case C10` returns `{"consensus": true, "value": 119410, "votes": 2, "models": ["openrouter:cohere/north-mini-code:free", "groq:qwen/qwen3.8-27b"]}`, `matches_reference: false`.

**Selected case: C10**, the only one where the shared wrong value wins **both** quorums: the third wrong vote (Dots) is outside the panel, so widening to 3-of-5 adds a wrong vote instead of an independent one. C15 shows the opposite effect (3-of-5 turns a wrong consensus into an abstention), and C02 shows the cost (3-of-5 abstains where the panel was right).

## 2. Identification — C10

| Model | In 2-of-3 panel | Verdict | Value |
|---|---|---|---|
| openai/gpt-oss-120b (Groq) | yes | correct | 558980 |
| openai/gpt-oss-20b (Groq) | no | correct | 558980 |
| cohere/north-mini-code:free (OpenRouter) | yes | incorrect | 119410 |
| qwen/qwen3.8-27b (Groq) | yes | incorrect | 119410 |
| dots-studio/dots-3-note-preview:free (OpenRouter) | no | incorrect | 119410 |

Question C10 (family F2b): revenue excl. VAT, in cents, of the orders placed by customers exactly 25 years old **at the time of the order**. Independent reference ([`reference-td1.csv`](../../td1/data/references/reference-td1.csv)): **558980**. Gap: **439570 cents**. All five cells are attempt 1; replaying the five stored SQL statements on the base gives exactly the values in the traces.

## 3. Faulty SQL clause

Completed age 25 at the order date ⇔ `date(o.date,'-26 years') < birth_date <= date(o.date,'-25 years')`. This window covers **two** situations:

- **(a)** year difference = 25 **and** birthday already reached in the order year;
- **(b)** year difference = 26 **and** birthday **not yet** reached. Real example: C007, born 2000-11-30, orders on 2026-01-20: year difference 26, but turns 26 only on 2026-11-30, so is still 25.

Faulty queries, verbatim from the traces:

```sql
-- cohere/north-mini-code:free -> 119410
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE CAST(strftime('%Y', o.date) - strftime('%Y', c.birth_date) AS INTEGER) = 25
  AND CAST(strftime('%m-%d', o.date) >= CAST(strftime('%m-%d', c.birth_date) AS TEXT) AS INTEGER) = 1;

-- qwen/qwen3.8-27b -> 119410
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE ((strftime('%Y', o.date) - strftime('%Y', c.birth_date)) = 25
       AND (strftime('%m', o.date) || strftime('%d', o.date)) >= (strftime('%m', c.birth_date) || strftime('%d', c.birth_date)))
   OR ((strftime('%Y', o.date) - strftime('%Y', c.birth_date)) = 24
       AND (strftime('%m', o.date) || strftime('%d', o.date)) < (strftime('%m', c.birth_date) || strftime('%d', c.birth_date)));

-- dots-studio/dots-3-note-preview:free -> 119410
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER) = 25
  AND (CAST(strftime('%m', o.date) AS INTEGER) > CAST(strftime('%m', c.birth_date) AS INTEGER)
       OR (CAST(strftime('%m', o.date) AS INTEGER) = CAST(strftime('%m', c.birth_date) AS INTEGER)
           AND CAST(strftime('%d', o.date) AS INTEGER) >= CAST(strftime('%d', c.birth_date) AS INTEGER)));
```

Correct query for comparison (gpt-oss-120b, 558980): `WHERE date(o.date) >= date(c.birth_date, '+25 years') AND date(o.date) < date(c.birth_date, '+26 years')`.

**Root cause (the `WHERE` condition):**

- **Cohere and Dots** test only (a): `year difference = 25 AND birthday reached`. Case (b) is never tested.
- **Qwen** adds a second branch but writes `= 24` instead of `= 26`: `year difference 24 AND birthday not reached` describes a customer aged **23**. On the base this branch matches **0 order lines**, so Qwen also computes (a) only.
- Three different syntaxes (`'%m-%d'` string, `'%m'||'%d'` concatenation, integers), three providers, **one shared logical gap**, hence one identical wrong value. `COALESCE` and the absence of any SQL error make 119410 look plausible.

## 4. Delta diagnostic query (executed on `data/boutique.sqlite`)

Rows counted by the reference but missed by the three faulty queries ([`scripts/delta_c10.sql`](scripts/delta_c10.sql)):

```sql
SELECT c.customer_id, c.birth_date,
       COUNT(*) AS order_lines,
       SUM(o.quantity_product * p.price) AS revenue_cents
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN product p ON p.product_id = o.product_id
WHERE c.birth_date > date(o.date, '-26 years')                 -- reference window
  AND c.birth_date <= date(o.date, '-25 years')
  AND NOT (                                                    -- faulty condition
    CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER) = 25
    AND strftime('%m-%d', o.date) >= strftime('%m-%d', c.birth_date)
  )
GROUP BY c.customer_id, c.birth_date
ORDER BY c.customer_id;
```

| customer_id | birth_date | order lines | first order | last order | revenue_cents |
|---|---|---|---|---|---|
| C004 | 2000-09-25 | 17 | 2026-01-22 | 2026-06-15 | 150260 |
| C005 | 2000-09-26 | 20 | 2026-01-06 | 2026-08-29 | 150240 |
| C007 | 2000-11-30 | 18 | 2026-01-20 | 2026-08-19 | 118740 |
| C022 | 2000-08-14 | 4 | 2026-04-01 | 2026-05-25 | 20330 |
| **Total** | | **59** | | | **439570** |

- **119410 + 439570 = 558980**: the four customers account for the entire gap, to the cent. All were born in 2000 and ordered in 2026 before their 26th birthday (case b).
- **Wrongly added rows:** the inverse query (faulty condition true, reference window false) returns **0 rows**. The error is a pure omission.
- One-line control ([`scripts/check_c10.sql`](scripts/check_c10.sql)): `(reference, case a only, case b missed) = (558980, 119410, 439570)`.

## 5. Independent check

Not reusing any SQL window: Python reads every order line and computes the completed age at the order date as `year difference − 1 if (month, day) of the order < (month, day) of the birth`. Age-25 revenue = **558980** (equals the reference); of which orders with year difference 26 = **439570** (equals the delta).

## 6. Mechanism illustrated — DEMO-VOTE (*constructed teaching example, not model output*)

One-row toy table: sale on 2026-01-01, 100 cents; period [2026-01-01, 2026-01-02). `sale_date > '2026-01-01'` → **0** (the boundary day is excluded); `sale_date >= '2026-01-01'` → **100**. Proposals [0, 0, 100], 2-of-3 → **0 kept with 2 votes**, reference 100. The vote measures agreement, not correctness. C10 is the same mechanism on real data: a shared boundary omission (case b) outvotes the right answer.

## 7. Consequence for checking

- **A quorum only protects against independent errors.** On C10 three families share the same shortcut; raising n from 3 to 5 made the wrong consensus stronger (3 votes).
- For the age families (F2, F2b), a free-model quorum is not enough for a figure shown to a customer or a payout: a **deterministic check** is required. This is the `reference` check of pair C's rule ([`../README.md`](../README.md), section 3.4), which rejects 119410 on C10.
- Complementary test before trusting a query: a fixed set of boundary customers (birthday the day before, the day of and the day after the order date; year difference 25 versus 26).
- 3-of-5 is not uniformly safer than 2-of-3: it fixes C15, abstains on C02 where the panel was right, and changes nothing on C10.
- Limitation: one batch of 20 questions × 5 models shows a mechanism, not an error rate.
