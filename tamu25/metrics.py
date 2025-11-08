import logging
import math
from typing import Sequence

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def dcg_at_k(rels: Sequence[int], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(rels[:k], start=1):
        dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg


def ndcg_at_k(rels: Sequence[int], k: int) -> float:
    dcg = dcg_at_k(rels, k)
    ideal = sorted(rels, reverse=True)
    idcg = dcg_at_k(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg


def precision_at_k(bin_rels: Sequence[int], k: int) -> float:
    top = bin_rels[:k]
    if not top:
        return 0.0
    return sum(top) / len(top)


def recall_at_k(bin_rels: Sequence[int], total_relevant: int, k: int) -> float:
    if total_relevant == 0:
        return 0.0
    return sum(bin_rels[:k]) / total_relevant


def average_precision(bin_rels: Sequence[int], total_relevant: int, k: int) -> float:
    if total_relevant == 0:
        return 0.0
    ap_sum = 0.0
    hit = 0
    for i, rel in enumerate(bin_rels[:k], start=1):
        if rel == 1:
            hit += 1
            ap_sum += hit / i
    return ap_sum / total_relevant
