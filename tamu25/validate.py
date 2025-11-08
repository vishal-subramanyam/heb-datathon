from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _load_json(path: str | Path) -> dict[str, any] | list[any]:
    file_path = Path(path)
    if not file_path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")
    else:
        logger.debug(f"File found: {path}")

    logger.debug(f"Loading JSON from: {path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_products(products_raw: dict[str, any] | list[any]) -> set[str]:
    """
    Allows:
      - ["001","002",...]
      - [{"product_id": "..."}]
    """
    ids: set[str] = set()
    if isinstance(products_raw, list):
        if not products_raw:
            return ids
        if isinstance(products_raw[0], str):
            ids = set(products_raw)
        else:
            for p in products_raw:
                pid = p.get("product_id")
                if pid:
                    ids.add(pid)
    return ids


def validate_submission(
    submission_path: str | Path,
    products_path: str | Path,
    queries_real_path: str | Path | None,
    queries_synth_path: str | Path,
    team: str,
    max_team_dirs: int = 1,
) -> dict[str, any]:
    """Validate team submission according to DSCOE Datathon rules."""
    report: dict[str, any] = {
        "team": team,
        "status": "failed",
        "errors": [],
        "warnings": [],
        "queries_checked": 0,
        "avg_depth": None,
    }

    submission_file = Path(submission_path)
    if not submission_file.exists():
        logger.error(f"submission file not found: {submission_path}")
        report["errors"].append(f"submission file not found: {submission_path}")
        return report
    logger.info(f"validating submission file: {submission_path}")
    # load reference
    logger.info(f"loading products from: {products_path}")
    products_raw = _load_json(products_path)

    if queries_real_path is not None:
        logger.info(f"loading real queries from: {queries_real_path}")
        queries_real = _load_json(queries_real_path)
    else:
        logger.info("no real queries provided, validating synthetic queries only")
        queries_real = []

    logger.info(f"loading synthetic queries from: {queries_synth_path}")
    queries_synth = _load_json(queries_synth_path)
    logger.debug("extracting valid products")
    valid_products = _extract_products(products_raw)

    required_queries: set[str] = set()
    for q in queries_real:
        required_queries.add(q["query_id"])
    for q in queries_synth:
        required_queries.add(q["query_id"])
    logger.debug(f"total required queries: {len(required_queries)}")
    # load submission
    logger.info(f"loading submission from {submission_path}")
    submission = _load_json(submission_path)
    if not isinstance(submission, list):
        report["errors"].append("submission must be a JSON array of objects")
        return report

    per_query = defaultdict(list)
    seen_pairs: set[tuple[str, str]] = set()
    duplicate_pairs = []

    for row in submission:
        if not isinstance(row, dict):
            report["errors"].append(f"submission rows must be objects, got: {row}")
            continue
        qid = row.get("query_id")
        rank = row.get("rank")
        pid = row.get("product_id")

        if qid is None or rank is None or pid is None:
            report["errors"].append(f"row missing field(s): {row}")
            continue

        # duplicates
        pair = (qid, pid)
        if pair in seen_pairs:
            duplicate_pairs.append({"query_id": qid, "product_id": pid})
        seen_pairs.add(pair)

        # product check
        if pid not in valid_products:
            report["errors"].append(f"unknown product_id '{pid}' for query_id '{qid}'")

        per_query[qid].append((rank, pid))

    # coverage check
    missing_queries = [qid for qid in required_queries if qid not in per_query]
    if missing_queries:
        report["errors"].append(f"missing {len(missing_queries)} queries from submission")
        report["warnings"].append({"missing_queries_sample": missing_queries[:20]})

    # per-query checks
    total_depth = 0
    qcount = 0
    for qid, rows in per_query.items():
        qcount += 1
        rows_sorted = sorted(rows, key=lambda x: x[0])
        total_depth += len(rows_sorted)

        if len(rows_sorted) < 30:
            report["errors"].append(f"query '{qid}' has only {len(rows_sorted)} results, need at least 30")

        expected = 1
        for r, _ in rows_sorted:
            if r != expected:
                report["errors"].append(
                    f"query '{qid}' ranks must be continuous starting at 1. found {r}, expected {expected}"
                )
                break
            expected += 1

    report["queries_checked"] = qcount
    report["avg_depth"] = round(total_depth / qcount, 2) if qcount else 0

    if duplicate_pairs:
        report["errors"].append(f"found duplicate (query_id, product_id) pairs: {duplicate_pairs[:10]}")

    # final status
    if report["errors"]:
        report["status"] = "failed"
    else:
        report["status"] = "passed"

    return report
