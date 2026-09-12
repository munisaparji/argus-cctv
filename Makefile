PYTHON ?= python
DEVICE ?= auto
.PHONY: setup demo test lint types api ui data features train eval batch-vlm docs
setup:
	$(PYTHON) -m pip install -e ".[dev]"
	cd apps/console && npm ci
	$(PYTHON) -m argus.cli schema
	cd apps/console && npm run types
demo:
	$(PYTHON) -m argus.cli demo
	cd apps/console && npm run build
	@echo Start the console with: make api
test:
	$(PYTHON) -m pytest -q
lint:
	$(PYTHON) -m ruff check src scripts tests
	$(PYTHON) -m mypy src/argus/schema src/argus/modules --follow-imports=silent
types:
	$(PYTHON) -m argus.cli schema
	cd apps/console && npm run types
api:
	$(PYTHON) -m argus.cli serve
ui:
	cd apps/console && npm run dev
data:
	$(PYTHON) -m argus.cli data
features:
	$(PYTHON) scripts/features.py $(VIDEO) --device $(DEVICE)
train:
	$(PYTHON) scripts/train/detector.py --index data/index/ucf_crime.parquet
eval:
	$(PYTHON) -m argus.cli eval
batch-vlm:
	$(PYTHON) scripts/batch_vlm.py --manifest data/cache/vlm_manifest.json
docs:
	$(PYTHON) -m mkdocs build
