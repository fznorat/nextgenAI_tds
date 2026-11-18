"""Tests of Orchestrateur.vote_k_sur_n (TD 2, pair A). No network, no model call.

  python3 td2/A/scripts/test_vote.py

Exit code 0 and the line "all tests passed" if every check holds.
"""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

skeleton_path = Path(__file__).with_name("skeleton-multi-llm-en.py")
spec = importlib.util.spec_from_file_location("skeleton", skeleton_path)
skeleton = importlib.util.module_from_spec(spec)
sys.modules["skeleton"] = skeleton
spec.loader.exec_module(skeleton)


def vote(proposals, k):
    return skeleton.Orchestrateur.vote_k_sur_n(None, proposals, k)


def member(name, value, provider = "p"):
    return SimpleNamespace(provider = provider, model_requested = name, value = value,
                           verdict = "executed" if value is not None else "error")


failures = 0


def check(label, condition):
    global failures
    print("ok  " if condition else "FAIL", label)
    failures += 0 if condition else 1


def refused(proposals, k):
    try:
        vote(proposals, k)
    except ValueError:
        return True
    return False


# contract point 2: k must be a strict majority
check("k = 1 of 3 refused", refused([member("a", 1), member("b", 1), member("c", 1)], 1))
check("k = 4 of 3 refused", refused([member("a", 1), member("b", 1), member("c", 1)], 4))
check("k = 2 of 4 refused (2 is not more than 4 // 2)", refused([member("a", 1), member("b", 1), member("c", 1), member("d", 1)], 2))
check("empty panel refused", refused([], 1))
# contract point 3: duplicates
check("duplicate (provider, model) refused", refused([member("a", 1), member("a", 1), member("c", 1)], 2))
check("same model name at another provider is not a duplicate", not refused([member("a", 1, "p1"), member("a", 1, "p2"), member("c", 1)], 2))
check("a duplicate in error is also refused", refused([member("a", None), member("a", 1), member("c", 1)], 2))
# contract point 4: consensus
result = vote([member("a", 100), member("b", 100), member("c", 7)], 2)
check("2 of 3 agree: consensus on 100 with 2 votes", result["consensus"] is True and result["value"] == 100 and result["votes"] == 2 and len(result["models"]) == 2)
result = vote([member("a", 0), member("b", 0), member("c", 3)], 2)
check("0 is a value: consensus on 0", result["consensus"] is True and result["value"] == 0)
# contract point 5: abstention, never an invented value
result = vote([member("a", 1), member("b", 2), member("c", 3)], 2)
check("three different values: abstain, value None, votes 1, no models", result["consensus"] is False and result["value"] is None and result["votes"] == 1 and result["models"] == [])
# contract point 1: an unavailable member stays in n and casts no vote
result = vote([member("a", 5), member("b", 5), member("c", 7), member("d", 7), member("e", None)], 3)
check("3-of-5, split 2-2 plus one unavailable: abstain with 2 votes", result["consensus"] is False and result["votes"] == 2)
result = vote([member("a", 100), member("b", None), member("c", 7)], 2)
check("2-of-3 with one unavailable and no agreement: abstain with 1 vote", result["consensus"] is False and result["votes"] == 1)
result = vote([member("a", None), member("b", None), member("c", None)], 2)
check("nobody voted: abstain with 0 votes", result["consensus"] is False and result["votes"] == 0)
# a wrong consensus is still a consensus: the vote never sees the reference
result = vote([member("a", 0), member("b", 0), member("c", 100)], 2)
check("[0, 0, 100] keeps 0 (the vote does not know the reference 100)", result["consensus"] is True and result["value"] == 0)
# a strict majority leaves a single possible winner
check("3-of-5 with a 3-2 split keeps the 3", vote([member("a", 1), member("b", 1), member("c", 1), member("d", 2), member("e", 2)], 3)["value"] == 1)

print("all tests passed" if failures == 0 else str(failures) + " test(s) failed")
sys.exit(1 if failures else 0)
