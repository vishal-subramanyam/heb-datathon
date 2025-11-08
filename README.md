# :brain: TAMU-25 Datathon Offline Evaluation

### Real + Synthetic Golden Sets • Multi-Team GitLab CI • Poetry Package :mortar_board: `tamu25` :mortar_board:

---

## :clipboard: Overview

This repository hosts the **official offline evaluation pipeline** for the 
**TAMU-25 H-E-B Datathon**, built by DSCOE AIML.
Each team submits ranked predictions for all queries, and the GitLab CI pipeline:
1. Validates format and coverage (`tamu25 validate`)
2. Scores results on **synthetic LLM** golden sets (`tamu25 evaulaate`)
3. Produces metrics: `nDCG@10`, `MAP@10`, `P@5`, `R@30` and `composite`
4. Publishes artifacts (`validation_report.json`, `score_report.json`) for the leaderboard

---

## :toolbox: Installation (Poetry Environment)

```bash
# clone the repo
git clone TBD/tamu-25.git
cd tamu-25
# install dependencies via Poetry
pip install poetry
poetry install
```

### Verify console scripts

```bash
poetry run tamu25 --help
poetry run tamu25 validate --help
poetry run tamu25 evaulaate --help
```

---

## :building_construction: Repository Structure

```
tamu-25
│
├─ pyproject.toml                ← Poetry project for `tamu25`
├─ tamu25/                       ← Python package (metrics + CLI)
│   │
│   ├─ __init__.py
│   ├─ validate.py
│   ├─ evaluate.py
│   ├─ metrics.py
│
├─ cli
│   │                    
│   ├─ main.py
│
├─ data/                         ← Golden datasets
│   │
│   ├─ products.json
│   ├─ queries_real.json
│   ├─ queries_synth.json
│   ├─ labels_real.json
│   ├─ labels_synth.json
│
├─ teams/                        ← Team submission folders
│   │
│   ├─ team_alpha/submission.json
│   ├─ team_bravo/submission.json
│   └─ ...
│
├─ tests/                        ← Unit & CLI tests
│   │
│   ├─ data/                     ← Example datasets for testing
│   ├─ test_validation.py
│   ├─ test_evalulate.py
│   ├─ test_cli.py
│   └─ conftest.py
│
└─ .gitlab-ci.yml                ← CI pipeline (test → validate → score)
```

---

## :repeat: Submission Process

Teams are allowed to **resubmit multiple times** during the Datathon to improve their ranking.

### :bulb: Key Principles

- Each submission triggers a **new pipeline run**.
- Your **latest successful score** per team replaces previous scores on the leaderboard.
- Earlier MRs remain archived for transparency and reproducibility.

---

## :test_tube: Example Usage

### Validate a Submission

```bash
poetry run tamu25 validate \
  --submission teams/team_echo/submission.json \
  --products data/products.json \
  --queries_synth data/queries_synth_train.json \
  --team team_echo \
  --out validation_report.json

```
or

```bash
make validate TEAM=team_alpha
```

Output example:

```json
{
  "team": "team_echo",
  "status": "failed",
  "errors": [
    "missing 288 queries from submission"
  ],
  "warnings": [
    {
      "missing_queries_sample": [
        "s171",
        "s147",
        "s445",
        "s563",
        "s244",
        "s128",
        "s289",
        "s168",
        "s353",
        "s341",
        "s441",
        "s272",
        "s90",
        "s292",
        "s295",
        "s121",
        "s126",
        "s536",
        "s3",
        "s486"
      ]
    }
  ],
  "queries_checked": 191,
  "avg_depth": 40.0
}
```
---

### Evaluate Scores

```bash
poetry run tamu25 evaluate \
  --submission teams/team_echo/submission.json \
  --labels_synth data/labels_synth_train.json \
  --team team_echo \
  --out score_report.json
```
or

```bash
make evaluate TEAM=team_echo
```

Output example:

```json
{
  "team": "team_echo",
  "synthetic": {
    "nDCG@10": 0.0,
    "AP@20": 0.0,
    "P@10": 0.0,
    "R@30": 0.0,
    "composite": 0.0,
    "queries_scored": 191
  },
  "combined": {
    "weighted_final": 0.0,
    "weights": {
      "synthetic": 1.0
    }
  }
}
```

---

## :jigsaw: Multi-Team GitLab Workflow

- All teams share **one repository**.
- Each team has a dedicated folder under `/teams/<team_name>/submission.json`.
- The CI automatically detects which team changed files and validates only that folder.

### Branch & MR Naming
| Purpose | Convention | Example |
|----------|-------------|----------|
| Branch   | `team_<name>/submission-run-<N>` | `team_alpha/submission-run-01` |
| MR Title | `<team_name> \| submission #<N> \| short description` | `team_alpha \| submission #1 \| reranker tuned` |

---

## :repeat: Resubmission Process
Teams are allowed to **resubmit multiple times** during the Datathon to improve their ranking.

### :bulb: Key Principles
- Each resubmission triggers a **new pipeline run**.
- Your **latest successful score** per team replaces previous scores on the leaderboard.
- Earlier MRs remain archived for transparency and reproducibility.
### :ladder: Step-by-Step
1. **Create a new branch for each run**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b team_<name>/submission-run-<N>
   ```
2. **Replace your submission file**
   ```
   teams/<team_name>/submission.json
   ```
3. **Commit & push**
   ```bash
   git add teams/<team_name>/submission.json
   git commit -m "team_<name> | submission run <N>"
   git push origin team_<name>/submission-run-<N>
   ```
4. **Open a Merge Request**
   - Target branch: `main`
   - MR Title: `team_<name> | submission #<N> | <description>`
   - The CI pipeline runs automatically.
5. **Monitor the pipeline**
   - Stage 1: `unit_tests` → verifies integrity and package
   - Stage 2: `validate_submission` → checks schema and coverage
   - Stage 3: `score_submission` → computes metrics
   - Stage 4: `presist_score` → commits and presist score and metadata
   - Stage 5: `build_leaderboard` → builds and commits leaderboard 
6. **Review Results**
   - Check MR → CI → Artifacts:  
     - `validation_report.json`
     - `score_report.json`
     - `metadata.json` (team, run id, timestamp)
   - Only successful `score_submission` results are published.
7. **Limits (if enforced by organizers)**
   - Teams may be limited to **N runs/day**.
   - Submissions failing validation **do not count** toward leaderboard.

---

## :abacus: Evaluation Logic
| Metric | Meaning | Primary Use |
|---------|----------|-------------|
| **nDCG@10** | Ranking fidelity (graded relevance, 0–3) | Leaderboard |
| **MAP@10** | Overall precision across ranks | Leaderboard |
| **P@5** | User-facing accuracy in top results | Leaderboard |
| **R@30** | Coverage of relevant items | Leaderboard |
| **Composite(q)** | \[0.30 · nDCG@10(q) + 0.30 · AP@20(q) + 0.25 · R@30(q) + 0.15 · P@10(q)\] | Leaderboard |

**Weighted Final Score:**
\[
Score = 0.0 \times composite_{\text{real}} + 1.0 \times composite_{\text{synthetic}}
\]

---

## :test_tube: Running Tests Locally

```bash
poetry run pytest -q
```
Tests include:
- Validation rules (missing queries, duplicates, rank continuity, etc.)
- Metric correctness and output contract
- CLI integration (console scripts)
- End-to-end JSON generation

or

```bash
make unittest
```

---

## :bricks: GitLab CI Pipeline

### Stages
| Stage | Description | Artifacts |
|--------|--------------|------------|
| **test** | Run unit + CLI tests with pytest | `pytest-junit.xml` |
| **validate** | Validate team submission | `validation_report.json` |
| **score** | Evaluate metrics & compute leaderboard scores | `score_report.json`, `metadata.json` |
### Trigger Rules
- Automatically runs on **pushes to `main`** that modifies `teams/*/submission.json`
- Publishes artifacts under each MR for leaderboard integration

---

## :page_facing_up: Submission File Format

Your team's submission must be a **JSON file** containing an array of ranked search results for all queries. Each result object specifies which product to return at what rank for a given query.

### Schema Structure
```json
[
  {
    "query_id": "Q001",
    "rank": 1,
    "product_id": "10045036"
  },
  {
    "query_id": "Q001", 
    "rank": 2,
    "product_id": "10048008"
  },
  ...
]
```

### Field Descriptions
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `query_id` | String | Unique identifier for the search query | `"Q001"`, `"s7"` |
| `rank` | Integer | Position in search results (1-based ranking) | `1`, `2`, `3`, ..., `10` |
| `product_id` | String | Unique identifier for the H-E-B product | `"10045036"` |

Example submission file live under `teams/team_echo/submission.json`. 
That demonstrates the expected schema and the ranking logic.


### Requirements
- **Complete Coverage**: Must include results for every query in both `queries_real.json` and `queries_synth_test.json`
- **Minimum Depth**: At least **30 ranked results per query** (rank 1 through 30)
- **Sequential Ranking**: Ranks must be strictly sequential (1, 2, 3, ...) with no gaps
- **Valid Products**: All `product_id` values must exist in the `data/products.json` catalog
- **Uniqueness**: Each `(query_id, product_id)` combination must be unique (no duplicate products per query)

### Example Entry Explanation
```json
{"query_id": "s7", "rank": 1, "product_id": "10045036"}
```
This means: For query `s7` ("ready-to-eat BBQ chicken"), rank the product `10045036` ("H-E-B Fish Market Party Tray - Seasoned Shrimp Cocktail") as the **#1 most relevant result**.

---

## :receipt: Validation Rules Summary

:heavy_check_mark: Must be JSON array 
:heavy_check_mark: At least **30 results per query** 
:heavy_check_mark: Ranks strictly sequential (1, 2, 3, ...) 
:heavy_check_mark: Each `(query_id, product_id)` unique 
:heavy_check_mark: All queries in both real + synthetic sets covered, if applicble. 
:heavy_check_mark: All product_ids exist in catalog (`data/products.json`)

> **Note:** Violations fail validation and block scoring.

---

## :brain: About the Golden Sets

The evaluation pipeline uses multiple datasets to test different aspects of your search algorithm. Each dataset serves a specific purpose in measuring search quality and relevance understanding.

### Core Datasets

| Dataset | Source | Purpose | Schema |
|----------|---------|----------|---------|
| **`products.json`** | H-E-B product catalog | Complete product database for validation and search | ```{product_id, title, description, brand, category_path, safety_warning, ingredients}``` |
| **`queries_synth_train.json`** | LLM-generated queries | Training/validation queries for semantic understanding | `{query_id, query}` |
| **`labels_synth_train.json`** | LLM-generated relevance labels | Training/validation ground truth for synthetic queries | `{query_id, product_id, relevance}` |
| **`queries_synth_test.json`** | LLM-generated queries | Final evaluation queries for leaderboard scoring | `{query_id, query}` |

### Dataset Details

#### **Products Catalog (`products.json`)**
- **A small subset** from the H-E-B catalog
- Contains detailed product information including titles, descriptions, brands, categories, and ingredients
- Used for **validation**: All `product_id` values in your submission must exist in this catalog
- Used for **search context**: Your algorithm should leverage product metadata for better relevance matching

**Example Entry:**
```json
{
  "product_id": "10045036",
  "title": "H-E-B Fish Market Party Tray - Seasoned Shrimp Cocktail",
  "description": "Before everyone comes over to your place, pick up this generous-sized party tray...",
  "brand": "H-E-B",
  "category_path": "Meat & seafood -> Seafood -> Shrimp & shellfish",
  "safety_warning": "Contains: SHRIMP, MILK, ANCHOVY. Caution: CONTAINS SHELLS...",
  "ingredients": "shrimp (shrimp, water, salt), cocktail sauce..."
}
```

#### **Synthetic Datasets (LLM-Generated)**
- **Purpose**: Test semantic understanding, constraint handling, and edge cases
- **Queries**: Generated to cover diverse search intents, dietary restrictions, brand preferences, and product categories
- **Labels**: Relevance scores (0-3) based on semantic matching between query intent and product attributes
- **Training Set**: `queries_synth_train.json` + `labels_synth_train.json` 
- **Test Set**: `queries_synth_test.json`. **Will be used for final leaderboard scoring**

**Query Examples:**
- `"ready-to-eat BBQ chicken"` - Tests understanding of preparation requirements
- `"H-E-B pimento cheese spread"` - Tests brand-specific search
- `"lunch cheese spreads"` - Tests category understanding and meal context


#### **Relevance Scale**
| Score | Meaning | Description |
|-------|---------|-------------|
| **3** | Highly Relevant | Perfect match for query intent; customer would definitely click/buy |
| **2** | Moderately Relevant | Good match but not perfect; reasonable alternative |
| **1** | Slightly Relevant | Tangentially related; might be of interest |
| **0** | Not Relevant | No meaningful connection to query |

### Usage in Evaluation
- **Validation**: Your submission must cover **all queries** from both `queries_real.json` / `queries_synth_test.json`
- **Scoring**: Performance is measured separately on real vs. synthetic datasets, then combined. 
- **Final Score**: Weighted combination prioritizing synthetic performance (current weights: 0.0 × real + 1.0 × synthetic)


---

## :jigsaw: Example Datasets
Small-scale example datasets for unit testing live under `tests/data/`. 
They demonstrate the expected schema and label logic (0–3 relevance).

---

## :toolbox: Quick Start for Local Debugging

### Run both steps manually

```bash
# Validate
poetry run tamu25 validate \
  --submission teams/team_alpha/submission.json \
  --products tests/data/products.json \
  --queries_synth tests/data/queries_synth.json \
  --team team_alpha \
  --out validation_report.json
# Evaluate (only if validation passes)
poetry run tamu25 evaluate \
  --submission teams/team_alpha/submission.json \
  --labels_synth tests/data/labels_synth.json \
  --team team_alpha \
  --out score_report.json
```

or

```bash
# Validate
make validate TEAM=team_echo
# Evaluate (only if validation passes)
make evaluate TEAM=team_echo
```

---

## :trophy: Leaderboard Integration
After each MR:
1. `score_report.json` + `metadata.json` are ingested by the leaderboard backend. 
2. The **latest successful score per team** updates the public table.

---

## :handshake: Maintainers

**H-E-B DSCOE AIML Team**

- Leads: *Aidin Zadeh*, *Rajesh Chodavarapu*
- Maintainers: *Aidin Zadeh*, *Neda Zand* and *Mary Nam*

---
