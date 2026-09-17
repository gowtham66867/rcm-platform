#!/usr/bin/env python3
"""
Evaluation harness — does Moss semantic recall actually catch clawbacks that the
regex library misses, without flagging ordinary EOB lines?

Measures two configurations on the same labeled set:

    baseline   RecoupmentAgent(use_semantic=False)   regex only
    +moss      RecoupmentAgent()                     regex + Moss semantic pass

and reports precision / recall / F1 for each, plus per-query latency.

METHODOLOGY
-----------
Every line in EVAL_SET is HELD OUT: none appears in `recoupment_corpus.json`.
The positives are reworded the way a payer actually rewords an offset, so the
score reflects generalisation to unseen phrasing rather than memorisation of the
indexed corpus. Scoring is per line: a line counts as detected if the agent
emits any flag for it.

The negatives are the harder half. They carry dollar amounts and
adjustment-flavoured wording ("contractual adjustment", "sequestration
reduction", "appeal resulted in additional payment") precisely because a naive
similarity threshold flags them. Recall that costs precision is not a win — a
billing coordinator who gets 40 false flags per EOB stops reading them.

Usage:
    python eval_semantic.py                # human-readable report
    python eval_semantic.py --json out.json
    python eval_semantic.py --threshold 0.5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── held-out labeled set ──────────────────────────────────────────────────────
# (line, is_recoupment). Amounts included so the lines look like real EOB rows.

EVAL_SET: List[Tuple[str, bool]] = [
    # ---- positives: payer clawback wording, none of it in the corpus ---------
    ("OUTSTANDING NEG BAL WITH DIFFER                    18,020.11", True),
    ("Prior overpayment recovered on this remittance          2,415.00", True),
    ("Amount recouped per audit                                 940.55", True),
    ("Payment reduced to satisfy an earlier excess disbursement   1,204.00", True),
    ("We have withheld funds pending an overpayment resolution     880.00", True),
    ("Earlier remittance issued in your favor is being corrected   3,110.25", True),
    ("Money owed back to the plan has been netted from this check  5,600.00", True),
    ("This voucher is short paid to collect a previous duplicate   770.40", True),
    ("Plan exercising contractual right of recovery this cycle   12,000.00", True),
    ("Debit posted against your account for a prior credit        1,950.00", True),
    ("Reversal of payment for services later found non payable      615.75", True),
    ("Applied your outstanding provider receivable to this claim  4,325.00", True),
    ("Post payment review finding results in funds withheld       2,010.00", True),
    ("Adjustment reflects monies previously advanced in error       498.20", True),
    ("Balance due to plan subtracted from current disbursement    7,240.00", True),
    ("Claim reprocessed; original payment has been backed out     1,133.60", True),
    ("Refund demand outstanding - amount retained this remit      3,875.00", True),
    ("Collection activity offset against current claim payments   9,410.00", True),
    ("Negative carryover from the prior voucher applied here      1,620.00", True),
    ("Recovery of funds disbursed on a claim paid incorrectly       702.15", True),

    # ---- negatives: ordinary EOB language, several deliberately adversarial --
    ("CONTRACTUAL ADJUSTMENT PER PROVIDER AGREEMENT           1,240.00", False),
    ("Patient responsibility after plan payment                  150.00", False),
    ("Copayment due from member                                   25.00", False),
    ("Deductible applied to this service                         500.00", False),
    ("Coinsurance 20% owed by patient                            340.00", False),
    ("Service not covered under the member benefit plan          210.00", False),
    ("Charge exceeds allowed amount, not billable to member      189.45", False),
    ("Procedure bundled into another service on this claim         0.00", False),
    ("Total billed charges for services rendered              12,400.00", False),
    ("Total amount paid to provider                            8,300.00", False),
    ("Allowed amount per contracted rate                       6,720.00", False),
    ("Sequestration reduction applied per federal requirement    166.00", False),
    ("Appeal resulted in additional payment to provider          925.00", False),
    ("Corrected claim processed - additional payment issued      430.00", False),
    ("Interest paid on late adjudicated claim                     12.88", False),
    ("Coordination of benefits - primary payer paid first        775.00", False),
    ("Timely filing limit exceeded, claim denied                   0.00", False),
    ("Units billed exceed maximum allowed per day                  0.00", False),
    ("Provider is out of network for this member                 640.00", False),
    ("Claim forwarded to secondary payer for consideration       318.00", False),
    ("Authorization number on file for this admission              0.00", False),
    ("Check number 4471028 issued 03/14/2026                   8,300.00", False),
    ("Remittance advice summary page totals                   21,640.00", False),
    ("Diagnosis code inconsistent with procedure performed         0.00", False),
    ("No action required - this is an informational message        0.00", False),
]


# ── metrics ───────────────────────────────────────────────────────────────────


def _metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
    }


def evaluate(use_semantic: bool) -> Dict:
    """Run the full eval set through one agent configuration."""
    from agents.recoupment_agent import RecoupmentAgent

    agent = RecoupmentAgent(use_semantic=use_semantic)
    tp = fp = fn = tn = 0
    missed: List[str] = []
    false_alarms: List[str] = []
    started = time.perf_counter()

    for line, is_recoup in EVAL_SET:
        # One line per document so detection is scored per line.
        result = agent.run(line, "eval.pdf")
        detected = bool(result.flags)
        if is_recoup and detected:
            tp += 1
        elif is_recoup and not detected:
            fn += 1
            missed.append(line.strip())
        elif not is_recoup and detected:
            fp += 1
            src = result.flags[0].get("source", "?")
            false_alarms.append(f"[{src}] {line.strip()}")
        else:
            tn += 1

    wall_ms = (time.perf_counter() - started) * 1000.0
    out = _metrics(tp, fp, fn, tn)
    out["wall_ms_total"] = round(wall_ms, 1)
    out["wall_ms_per_line"] = round(wall_ms / len(EVAL_SET), 3)
    out["missed_recoupments"] = missed
    out["false_alarms"] = false_alarms
    return out


# ── reporting ─────────────────────────────────────────────────────────────────


def _row(label: str, m: Dict) -> str:
    return (
        f"  {label:<12} "
        f"precision={m['precision']:.3f}  "
        f"recall={m['recall']:.3f}  "
        f"f1={m['f1']:.3f}   "
        f"TP={m['true_positives']:<3} FP={m['false_positives']:<3} "
        f"FN={m['false_negatives']:<3} TN={m['true_negatives']:<3}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Moss semantic recall")
    parser.add_argument("--json", dest="json_out", help="write full results to this path")
    parser.add_argument("--threshold", type=float, help="override MOSS_SCORE_THRESHOLD")
    parser.add_argument("--alpha", type=float, help="override MOSS_ALPHA")
    args = parser.parse_args()

    if args.threshold is not None:
        os.environ["MOSS_SCORE_THRESHOLD"] = str(args.threshold)
    if args.alpha is not None:
        os.environ["MOSS_ALPHA"] = str(args.alpha)

    n_pos = sum(1 for _, y in EVAL_SET if y)
    print()
    print("=" * 78)
    print("  TexMed — recoupment detection eval (held-out set)")
    print(f"  {len(EVAL_SET)} lines: {n_pos} clawbacks, {len(EVAL_SET) - n_pos} benign")
    print("=" * 78)

    from agents.semantic_matcher import get_matcher

    matcher = get_matcher()
    moss_ready = False
    if matcher.enabled:
        print("\n  Warming Moss index...")
        moss_ready = matcher.warm()
    if not moss_ready:
        print(f"\n  ⚠  Moss unavailable — {matcher.disabled_reason}")
        print("     Reporting the regex-only baseline. Set MOSS_PROJECT_ID and")
        print("     MOSS_PROJECT_KEY to measure the semantic layer.")

    print("\n  Running baseline (regex only)...")
    baseline = evaluate(use_semantic=False)

    results = {"baseline": baseline, "moss_ready": moss_ready}
    print("\n" + "-" * 78)
    print(_row("baseline", baseline))

    if moss_ready:
        print("\n  Running regex + Moss semantic recall...")
        semantic = evaluate(use_semantic=True)
        results["with_moss"] = semantic
        print(_row("+ moss", semantic))

        d_recall = semantic["recall"] - baseline["recall"]
        d_prec = semantic["precision"] - baseline["precision"]
        caught = baseline["false_negatives"] - semantic["false_negatives"]
        print("-" * 78)
        print(f"\n  Δ recall     {d_recall:+.3f}   ({caught} clawback(s) the regex library missed)")
        print(f"  Δ precision  {d_prec:+.3f}")

        stats = matcher.stats()
        results["moss_stats"] = stats
        print(f"\n  Moss query latency   p50={stats['latency_ms_p50']} ms   "
              f"p95={stats['latency_ms_p95']} ms   max={stats['latency_ms_max']} ms")
        print(f"  Queries issued       {stats['queries']}")
        print(f"  Semantic flags       {stats['semantic_flags']}")

        if semantic["missed_recoupments"]:
            print(f"\n  Still missed ({len(semantic['missed_recoupments'])}):")
            for line in semantic["missed_recoupments"]:
                print(f"    · {line[:70]}")
        if semantic["false_alarms"]:
            print(f"\n  False alarms ({len(semantic['false_alarms'])}):")
            for line in semantic["false_alarms"]:
                print(f"    · {line[:70]}")
    else:
        print("-" * 78)
        print(f"\n  Baseline misses {baseline['false_negatives']} of {n_pos} clawbacks "
              f"({baseline['false_negatives'] / n_pos:.0%}) — this is the recall gap")
        print("  the Moss semantic layer is built to close.")

    print()
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(results, fh, indent=2)
        print(f"  Full results → {args.json_out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
