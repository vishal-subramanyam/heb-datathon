import json
import shutil
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    # assume tests/ lives at repo_root/tests
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def sample_data_dir(repo_root: Path) -> Path:
    # Expected example data from the earlier message:
    # tests/data/{products.json, queries_real.json, queries_synth.json,
    #             labels_real.json, labels_synth.json}
    d = repo_root / "tests" / "data"
    assert d.exists(), f"Missing example data at {d}"
    return d


@pytest.fixture(scope="function")
def workdir(tmp_path: Path, sample_data_dir: Path, repo_root: Path) -> Path:
    """
    Create a temp working directory with a copy of:
      - tests/data/* (products, queries, labels)
      - teams/team_alpha/submission.json (valid)
    """
    # Copy data
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    for name in [
        "products.json",
        "queries_real.json",
        "queries_synth.json",
        "labels_real.json",
        "labels_synth.json",
    ]:
        shutil.copy(sample_data_dir / name, tmp_path / "data" / name)
    # Copy a known-good team submission
    src_sub = repo_root / "teams" / "team_alpha" / "submission.json"
    dest_dir = tmp_path / "teams" / "team_alpha"
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_sub, dest_dir / "submission.json")
    return tmp_path


def read_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)
