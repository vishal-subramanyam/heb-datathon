from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

from .metrics import average_precision, ndcg_at_k, precision_at_k, recall_at_k

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _load_json(path: str | Path) -> any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_label_lookup(labels: list[dict[str, any]]) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    lookup: dict[str, dict[str, int]] = defaultdict(dict)
    relevant_counts: dict[str, int] = defaultdict(int)
    for row in labels:
        qid = row["query_id"]
        pid = row["product_id"]
        rel = row["relevance"]
        lookup[qid][pid] = rel
        if rel >= 1:
            relevant_counts[qid] += 1
    return lookup, relevant_counts


def evaluate_submission(
    submission_path: str | Path,
    labels_path: str | Path,
    k_list: tuple[int, ...] = (5, 10, 20),
) -> dict[str, any]:
    submission = _load_json(submission_path)
    labels = _load_json(labels_path)

    label_lookup, relevant_counts = _build_label_lookup(labels)

    # group submission
    per_query: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in submission:
        per_query[row["query_id"]].append((row["rank"], row["product_id"]))

    metrics_acc: dict[str, list[float]] = {
        "nDCG@10": [], "AP@20": [], "P@10": [], "R@30": [], "composite": []
    }

    for qid, rows in per_query.items():
        rows_sorted = sorted(rows, key=lambda x: x[0])
        rels: list[int] = []
        bin_rels: list[int] = []
        for _, pid in rows_sorted:
            rel = label_lookup[qid].get(pid, 0)
            rels.append(rel)
            bin_rels.append(1 if rel >= 1 else 0)

        total_rel = relevant_counts[qid]

        # Calculate individual metrics
        ndcg_10 = ndcg_at_k(rels, 10)
        ap_20 = average_precision(bin_rels, total_rel, 20)
        p_10 = precision_at_k(bin_rels, 10)
        r_30 = recall_at_k(bin_rels, total_rel, 30)
        
        # Calculate composite metric: 0.30 · nDCG@10 + 0.30 · AP@20 + 0.25 · R@30 + 0.15 · P@10
        composite = 0.30 * ndcg_10 + 0.30 * ap_20 + 0.25 * r_30 + 0.15 * p_10

        metrics_acc["nDCG@10"].append(ndcg_10)
        metrics_acc["AP@20"].append(ap_20)
        metrics_acc["P@10"].append(p_10)
        metrics_acc["R@30"].append(r_30)
        metrics_acc["composite"].append(composite)

    def _avg(lst: list[float]) -> float:
        return round(sum(lst) / len(lst), 4) if lst else 0.0

    return {
        "nDCG@10": _avg(metrics_acc["nDCG@10"]),
        "AP@20": _avg(metrics_acc["AP@20"]),
        "P@10": _avg(metrics_acc["P@10"]),
        "R@30": _avg(metrics_acc["R@30"]),
        "composite": _avg(metrics_acc["composite"]),
        "queries_scored": len(per_query),
    }


def full_evaluation(
    submission_path: str | Path,
    labels_real_path: str | Path | None,
    labels_synth_path: str | Path,
    team: str,
    w_real: float = 0.7,
    w_synth: float = 0.3,
) -> dict[str, any]:
    synth_metrics = evaluate_submission(submission_path, labels_synth_path)

    if labels_real_path is not None:
        real_metrics = evaluate_submission(submission_path, labels_real_path)
        final_score = round(
            w_real * real_metrics["composite"] + w_synth * synth_metrics["composite"],
            4,
        )
        return {
            "team": team,
            "real": real_metrics,
            "synthetic": synth_metrics,
            "combined": {
                "weighted_final": final_score,
                "weights": {"real": w_real, "synthetic": w_synth},
            },
        }
    else:
        # When only synthetic labels are available
        final_score = synth_metrics["composite"]
        return {
            "team": team,
            "synthetic": synth_metrics,
            "combined": {
                "weighted_final": final_score,
                "weights": {"synthetic": 1.0},
            },
        }
