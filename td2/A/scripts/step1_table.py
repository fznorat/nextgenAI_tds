"""Step 1 (TD2, pair A): 2-of-3 vs 3-of-5 vote table from stored TD1 traces. No network.
Usage: python3 step1_table.py --traces traces-td1.csv --reference reference-td1.csv --skeleton skeleton-multi-llm-en.py
"""
import argparse, csv, importlib.util, sys
from types import SimpleNamespace

parser = argparse.ArgumentParser()
parser.add_argument("--traces", required = True)
parser.add_argument("--reference", required = True)
parser.add_argument("--skeleton", default = "skeleton-multi-llm-en.py")
parser.add_argument("--out", default = "step1-table.csv")
args = parser.parse_args()

spec = importlib.util.spec_from_file_location("skeleton", args.skeleton)
skeleton = importlib.util.module_from_spec(spec)
sys.modules["skeleton"] = skeleton
spec.loader.exec_module(skeleton)

MODELS = {
    "A": ("groq", "openai/gpt-oss-120b"),
    "B": ("groq", "openai/gpt-oss-20b"),
    "C": ("openrouter", "cohere/north-mini-code:free"),
    "D": ("groq", "qwen/qwen3.8-27b"),
    "E": ("openrouter", "dots-studio/dots-3-note-preview:free"),
}
reference = {row["case_id"]: int(row["revenue_cents"]) for row in csv.DictReader(open(args.reference, newline = "", encoding = "utf-8"))}

last_attempt = {}
skipped_not_real = 0
with open(args.traces, newline = "", encoding = "utf-8") as trace_file:
    for row in csv.DictReader(trace_file):
        if row.get("nature", "real") != "real":
            skipped_not_real += 1   # only real cells are measured counts
            continue
        key = (row["provider"], row["model_requested"], row["case_id"])
        # the last attempt is the one with the highest `attempts`, whatever the order of the file
        if key not in last_attempt or int(row["attempts"] or 1) >= int(last_attempt[key]["attempts"] or 1):
            last_attempt[key] = row

def proposal(letter, case_id):
    provider, model = MODELS[letter]
    row = last_attempt[(provider, model, case_id)]
    voted = row["verdict"] in ("correct", "incorrect") and row["value"] not in ("", None)
    value = int(float(row["value"])) if voted else None
    return SimpleNamespace(provider = provider, model_requested = model, value = value, verdict = "executed" if voted else "error"), row["verdict"]

def vote(letters, k, case_id):
    return skeleton.Orchestrateur.vote_k_sur_n(None, [proposal(letter, case_id)[0] for letter in letters], k)

def text(decision):
    return str(decision["value"]) if decision["consensus"] else "abstain"

def versus(decision, case_id):
    if not decision["consensus"]:
        return "-"
    return "yes" if decision["value"] == reference[case_id] else "NO"

rows = []
for number in range(1, 21):
    case_id = "C%02d" % number
    decision_23 = vote("ACD", 2, case_id)
    decision_35 = vote("ABCDE", 3, case_id)
    row = {"case": case_id, "reference": reference[case_id]}
    for letter in "ABCDE":
        prop, verdict = proposal(letter, case_id)
        row[letter] = prop.value if prop.value is not None else "(" + verdict + ")"
    row["2of3_voters"] = str(sum(1 for letter in "ACD" if proposal(letter, case_id)[0].value is not None)) + "/3"
    row["3of5_voters"] = str(sum(1 for letter in "ABCDE" if proposal(letter, case_id)[0].value is not None)) + "/5"
    row["2of3"] = text(decision_23); row["2of3_votes"] = decision_23["votes"]; row["2of3_vs_ref"] = versus(decision_23, case_id)
    row["3of5"] = text(decision_35); row["3of5_votes"] = decision_35["votes"]; row["3of5_vs_ref"] = versus(decision_35, case_id)
    row["decision_changes"] = "YES" if row["2of3"] != row["3of5"] else ""
    rows.append(row)

with open(args.out, "w", newline = "") as handle:
    writer = csv.DictWriter(handle, fieldnames = list(rows[0]))
    writer.writeheader(); writer.writerows(rows)

for key in ("2of3", "3of5"):
    print(key, "| consensus:", sum(1 for r in rows if r[key + "_vs_ref"] != "-"), "| correct:", sum(1 for r in rows if r[key + "_vs_ref"] == "yes"),
          "| wrong:", [r["case"] for r in rows if r[key + "_vs_ref"] == "NO"], "| abstain:", [r["case"] for r in rows if r[key + "_vs_ref"] == "-"])
print("cells skipped because nature != real:", skipped_not_real)
print("decision changes:", [r["case"] for r in rows if r["decision_changes"]])
