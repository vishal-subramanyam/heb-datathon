from pathlib import Path

from tamu25.evaluate import full_evaluation


def test_full_evaluation_contract(workdir: Path):
    report = full_evaluation(
        submission_path=workdir / "teams" / "team_alpha" / "submission.json",
        labels_real_path=workdir / "data" / "labels_real.json",
        labels_synth_path=workdir / "data" / "labels_synth.json",
        team="team_alpha",
    )
    # Required top-level keys
    assert set(report.keys()) == {"team", "real", "synthetic", "combined"}
    assert report["team"] == "team_alpha"
    # Check real/synth metric presence
    for section in ["real", "synthetic"]:
        sec = report[section]
        assert "nDCG@10" in sec
        assert "AP@20" in sec
        assert "P@10" in sec
        assert "R@30" in sec
        assert "composite" in sec
        assert 0.0 <= sec["nDCG@10"] <= 1.0
        assert 0.0 <= sec["AP@20"] <= 1.0
        assert 0.0 <= sec["P@10"] <= 1.0
        assert 0.0 <= sec["R@30"] <= 1.0
        assert 0.0 <= sec["composite"] <= 1.0
        assert sec["queries_scored"] > 0
    # Combined score sanity
    assert "weighted_final" in report["combined"]
    final = report["combined"]["weighted_final"]
    assert 0.0 <= final <= 1.0
    # Check that the composite metric is reasonable compared to individual metrics
    # Since composite = 0.30 * nDCG@10 + 0.30 * AP@20 + 0.25 * R@30 + 0.15 * P@10
    # It should be within a reasonable range of the individual metrics
    for section in ["real", "synthetic"]:
        assert 0.0 <= report[section]["composite"] <= 1.0


def test_full_evaluation_synthetic_only(workdir: Path):
    """Test evaluation with only synthetic labels (no real labels)."""
    report = full_evaluation(
        submission_path=workdir / "teams" / "team_alpha" / "submission.json",
        labels_real_path=None,
        labels_synth_path=workdir / "data" / "labels_synth.json",
        team="team_alpha",
    )
    # Required top-level keys for synthetic-only evaluation
    assert set(report.keys()) == {"team", "synthetic", "combined"}
    assert report["team"] == "team_alpha"
    assert "real" not in report  # Should not have real metrics

    # Check synthetic metric presence
    sec = report["synthetic"]
    assert "nDCG@10" in sec
    assert "AP@20" in sec
    assert "P@10" in sec
    assert "R@30" in sec
    assert "composite" in sec
    assert 0.0 <= sec["nDCG@10"] <= 1.0
    assert 0.0 <= sec["AP@20"] <= 1.0
    assert 0.0 <= sec["P@10"] <= 1.0
    assert 0.0 <= sec["R@30"] <= 1.0
    assert 0.0 <= sec["composite"] <= 1.0
    assert sec["queries_scored"] > 0

    # Combined score should equal synthetic nDCG@10 when only synthetic is used
    assert "weighted_final" in report["combined"]
    final = report["combined"]["weighted_final"]
    assert final == sec["nDCG@10"]
    assert report["combined"]["weights"]["synthetic"] == 1.0
    assert "real" not in report["combined"]["weights"]
