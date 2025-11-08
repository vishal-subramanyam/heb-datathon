# Makefile
# --------
# Usage:
#   make validate TEAM=team_alpha
#   make evaluate TEAM=team_alpha
#   make info
#   make version
TEAM ?= team_alpha
OUT_DIR ?= .
SUBMISSION = teams/$(TEAM)/submission.json
PRODUCTS   = data/products.json
QREAL      = data/queries_real_train.json
QSYNTH     = data/queries_synth_train.json
LREAL      = data/labels_real_train.json
LSYNTH     = data/labels_synth_train.json
.PHONY: install validate evaluate all clean info version

lint: ## Lint and reformat the code
	@poetry run autoflake tamu25 tests scripts --remove-all-unused-imports --recursive --remove-unused-variables --in-place --exclude=__init__.py
	@poetry run black tamu25 tests scripts --line-length 120 -q
	@poetry run isort tamu25 tests scripts -q

unittest: ## Run unit-tests
	@poetry run pytest -s -v tests

install:
	@pip install poetry
	@poetry install

validate:
	poetry run tamu25 validate \
		--submission $(SUBMISSION) \
		--products $(PRODUCTS) \
		--queries_synth $(QSYNTH) \
		--team $(TEAM) \
		--out $(OUT_DIR)/validation_report.json
evaluate:
	poetry run tamu25 evaluate \
		--submission $(SUBMISSION) \
		--labels_synth $(LSYNTH) \
		--team $(TEAM) \
		--out $(OUT_DIR)/score_report.json
all: validate evaluate

clean:
	rm -f $(OUT_DIR)/validation_report.json $(OUT_DIR)/score_report.json

info:
	poetry run tamu25 info

version:
	poetry run tamu25 version
