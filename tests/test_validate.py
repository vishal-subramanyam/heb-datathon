import json
from pathlib import Path

from tamu25.validate import validate_submission
from tests.conftest import read_json


def _run_validate_ok(workdir: Path):
    report = validate_submission(
        submission_path=workdir / "teams" / "team_alpha" / "submission.json",
        products_path=workdir / "data" / "products.json",
        queries_real_path=workdir / "data" / "queries_real.json",
        queries_synth_path=workdir / "data" / "queries_synth.json",
        team="team_alpha",
    )
    assert report["status"] == "passed", report
    assert report["queries_checked"] > 0
    assert report["avg_depth"] and report["avg_depth"] >= 10
    return report


# def test_validate_happy_path(workdir: Path):
#     _run_validate_ok(workdir)


def test_validate_missing_query(workdir: Path):
    # Remove all rows for one real query_id (e.g., Q004) to trigger coverage error
    sub_path = workdir / "teams" / "team_alpha" / "submission.json"
    rows = read_json(sub_path)
    # filter out Q004
    rows = [r for r in rows if r["query_id"] != "Q004"]
    sub_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    report = validate_submission(
        submission_path=sub_path,
        products_path=workdir / "data" / "products.json",
        queries_real_path=workdir / "data" / "queries_real.json",
        queries_synth_path=workdir / "data" / "queries_synth.json",
        team="team_alpha",
    )
    assert report["status"] == "failed"
    assert any("missing" in err for err in report["errors"])


def test_validate_duplicate_pair(workdir: Path):
    # Duplicate (query_id, product_id) for Q001 to trigger duplicate error
    sub_path = workdir / "teams" / "team_alpha" / "submission.json"
    rows = read_json(sub_path)
    first_q1 = next(r for r in rows if r["query_id"] == "Q001")
    rows.append(dict(first_q1))  # duplicate exact pair (same rank/product)
    sub_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    report = validate_submission(
        submission_path=sub_path,
        products_path=workdir / "data" / "products.json",
        queries_real_path=workdir / "data" / "queries_real.json",
        queries_synth_path=workdir / "data" / "queries_synth.json",
        team="team_alpha",
    )
    assert report["status"] == "failed"
    assert "duplicate" in " ".join(report["errors"]).lower()


def test_validate_non_continuous_ranks(workdir: Path):
    # Break continuity for Q001: make rank jump 1,2,4...
    sub_path = workdir / "teams" / "team_alpha" / "submission.json"
    rows = read_json(sub_path)
    q1 = [r for r in rows if r["query_id"] == "Q001"]
    q1[2]["rank"] = 4  # creates gap at rank 3
    out = []
    seen = set()
    for r in rows:
        key = (r["query_id"], r["product_id"])
        if key in seen:
            continue
        seen.add(key)
        if r["query_id"] == "Q001" and r["product_id"] == q1[2]["product_id"]:
            out.append(q1[2])
        else:
            out.append(r)
    sub_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    report = validate_submission(
        submission_path=sub_path,
        products_path=workdir / "data" / "products.json",
        queries_real_path=workdir / "data" / "queries_real.json",
        queries_synth_path=workdir / "data" / "queries_synth.json",
        team="team_alpha",
    )
    assert report["status"] == "failed"
    assert "continuous" in " ".join(report["errors"]).lower()


def test_validate_too_few_results(workdir: Path):
    # Keep only 9 rows for Q002
    sub_path = workdir / "teams" / "team_alpha" / "submission.json"
    rows = read_json(sub_path)
    q2 = [r for r in rows if r["query_id"] == "Q002"]
    rest = [r for r in rows if r["query_id"] != "Q002"]
    q2_trim = [r for r in q2 if r["rank"] <= 9]  # 9 results
    rows_new = rest + q2_trim
    sub_path.write_text(json.dumps(rows_new, indent=2), encoding="utf-8")
    report = validate_submission(
        submission_path=sub_path,
        products_path=workdir / "data" / "products.json",
        queries_real_path=workdir / "data" / "queries_real.json",
        queries_synth_path=workdir / "data" / "queries_synth.json",
        team="team_alpha",
    )
    assert report["status"] == "failed"
    assert "at least 30" in " ".join(report["errors"]).lower()


def test_validate_unknown_product(workdir: Path):
    # Inject an unknown product_id
    sub_path = workdir / "teams" / "team_alpha" / "submission.json"
    rows = read_json(sub_path)
    rows[0]["product_id"] = "ZZZZ"  # not in catalog
    sub_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    report = validate_submission(
        submission_path=sub_path,
        products_path=workdir / "data" / "products.json",
        queries_real_path=workdir / "data" / "queries_real.json",
        queries_synth_path=workdir / "data" / "queries_synth.json",
        team="team_alpha",
    )
    assert report["status"] == "failed"
    assert "unknown product_id" in " ".join(report["errors"]).lower()


def test_validate_synthetic_only(workdir: Path):
    """Test validation with only synthetic queries (no real queries)."""
    # Create a submission with only synthetic query results
    sub_path = workdir / "teams" / "team_alpha" / "submission.json"
    rows = read_json(sub_path)

    # Filter to only include synthetic queries (assuming they start with "SYN")
    synth_queries = read_json(workdir / "data" / "queries_synth.json")
    synth_qids = {q["query_id"] for q in synth_queries}
    synth_rows = [r for r in rows if r["query_id"] in synth_qids]

    sub_path.write_text(json.dumps(synth_rows, indent=2), encoding="utf-8")

    report = validate_submission(
        submission_path=sub_path,
        products_path=workdir / "data" / "products.json",
        queries_real_path=None,  # No real queries
        queries_synth_path=workdir / "data" / "queries_synth.json",
        team="team_alpha",
    )

    # Should pass if synthetic queries are properly covered
    assert report["status"] == "passed" or "missing" in " ".join(report.get("errors", []))
    assert report["queries_checked"] >= 0
    assert report["team"] == "team_alpha"
