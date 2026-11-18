# NextGenAI — TD 1 to TD 3

Shared repository of **DIA 1, sub-group 3** for the module *Trustworthy generative AI* (ESILV).
One folder per session, each with its own report.

| Folder | Session | Report | Status |
|---|---|---|---|
| [`td1/`](td1/) | TD 1 — five models write SQL, measured against our own reference | [`td1/td1.md`](td1/td1.md) | Complete, 100/100 cells |
| [`td2/`](td2/) | TD 2 — the quorum, then the routing rule | [`td2/README.md`](td2/README.md) | Step 3 (pair C) complete; steps 1 and 2 with pairs A and B |
| [`td3/`](td3/) | TD 3 — configuration, cost and demonstration | [`td3/td3.md`](td3/td3.md) | Not started |

Each folder keeps its own `data/`, `analysis/`, `scripts/` and `outputs/` so a session can be
read and reproduced on its own. TD 2 reads the TD 1 traces in place (`td1/data/`) and makes no new
provider call.

## Group

- **Course:** Next Generation AI — ESILV, Didier Parisot
- **Members:** NORAT Faizan · PERKINS Luca · DE GENTILE Océane · SAAID Myriam ·
  KHADRAOUI Oussama · KUETE Richard · VERDES Adrian · SAMSON Clément
- **Student kit:** pack `2026-10-21` for TD 1, pack `2026-11-18-students-5` for TD 2

## Environment

- Windows, Python 3.12/3.13, virtual environment `.venv` (not committed)
- Access check: 5/5 required models passed on 17 October 2026
- Database and data integrity verified with the kit's verification script

```powershell
.\.venv\Scripts\python.exe verify-data.py      # from the student kit directory
.\.venv\Scripts\python.exe check_access.py
```

The access-check output stays local (`ready-for-td1.txt`, ignored by git).

## Reproducing the analyses

Every script is standard library only, reads committed files and makes no network call.

```powershell
# TD 1 — recompute the twenty references two independent ways
python td1/scripts/check_references.py <student-kit-dir> td1/data/references/reference-td1.csv

# TD 2 — per-family TD 1 rates, quorum behaviour, routing rule, deterministic check
python td2/scripts/family_rates_td2.py --print
python td2/scripts/atelier-routage.py                     # the kit's rule, before adaptation
python td2/scripts/atelier-routage-td2.py --table         # our rule
python td2/scripts/age_guard_td2.py <student-kit-dir>     # the reference check, executed
```

`<student-kit-dir>` is the local student kit that holds `data/boutique.sqlite`. The database is
supplied by the course and is not committed here.

## What this repository claims, and what it does not

- All results come from **real** calls (`nature = real`); replayed or synthetic material is labelled
  as such wherever it appears.
- One run per cell at temperature 0 on twenty questions supports a **routing hypothesis for this
  batch**, not a general error rate, a permanent model ranking, or any guarantee that a quorum
  avoids errors. TD 2 shows a case where it does not (`C10`).
- Prices and public indices come from the kit's dated snapshots. A missing price is written `N/A`,
  never 0.

## Security

Never commit API keys, passwords, `.env` files or credentials. Local environments and virtual
environments stay out of version control. Check every file before committing it to this public
repository.
