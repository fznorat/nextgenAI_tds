# TD 2 — Cross-review by pair A of pair B (Step 2, wrong consensus on C10)

Reviewer: pair A (PERKINS Luca NORAT Faizan). Session of 18 November 2026. Reviewed: [`../B/README.md`](../B/README.md) and the files of [`../B/`](../B/) at commit `4542736`.

## Reproduced?

Yes. Two ways, both on `data/boutique.sqlite` from the student kit (read-only), no model call:

1. **Pair B's own script** `python td2/B/scripts/pair_b_wrong_consensus.py --db <kit>/data/boutique.sqlite` produces an output **identical** to the committed `td2/B/outputs/wrong-consensus/pair_b_output.txt` (only the database path in one title line differs).
2. **Our own independent script** `review_check.py`, which does not reuse their SQL files:
   - reference window → **558980**; shared faulty clause (case a only) → **119410**; gap **439570**;
   - delta: **C004, C005, C007, C022**, 17 + 20 + 18 + 4 = **59 lines**, 150260 + 150240 + 118740 + 20330 = **439570**, same table as their section 4;
   - lines counted by the faulty clause and not by the reference: **0** (pure omission);
   - Qwen's `= 24` branch matches **0** lines;
   - independent Python age computation: age-25 revenue **558980**, of which year difference 26 **439570**.

Their cross-check with our `vote_k_sur_n` (8 decisions out of 8) agrees with our own table.

## Two things that are solid

1. **The proof closes to the cent and nothing is hidden.** 119410 + 439570 = 558980 per customer, the diagnostic query names the exact rows, and the inverse query shows nothing is wrongly added. This is the delta the page asks for.
2. **The cause is stated at clause level and the consequence for checking follows.** Three syntaxes, three providers, one logical gap (case b, year difference 26 with the birthday not yet reached, is never tested), and Qwen's `= 24` branch is shown to be a dead branch. Hence a vote cannot catch it and a deterministic recomputation can; C10 is correctly chosen because the wrong value wins **both** quorums. The case is real (`nature = real`) and DEMO-VOTE is kept separate and labelled.

## Remaining remarks (none blocks the hand-in)

1. **The delta query's window is written differently from the reference query** (`birth_date > date(o.date, '-26 years') AND birth_date <= date(o.date, '-25 years')` against `o.date >= date(birth_date, '+25 years') AND o.date < date(birth_date, '+26 years')`). They agree on this base (no customer is born on 29 February, and both give 558980), but the report should say so in one line, because the two forms are not equivalent for a 29 February birth.
2. **Section 7 wording.** "Raising n from 3 to 5 made the wrong consensus stronger (3 votes)": the extra vote comes from Dots, which shares the same gap, so the larger quorum added a **correlated** vote, not an independent one. The report already argues the idea; the sentence should say it.
3. For the sub-group: `td2/B/groupe-A.md` (pair B's review of our Step 1) is still the generated placeholder and has not been written yet.

Verdict: the analysis is correct, complete and reproducible. The files are in the repository and the links resolve.
