.PHONY: generate ensure-artifacts demo test build smoke figures down

DATA_DIR ?= data
ARTIFACTS := \
	$(DATA_DIR)/observations.parquet \
	$(DATA_DIR)/detections.parquet \
	$(DATA_DIR)/incidents.parquet \
	$(DATA_DIR)/isolation_forest.joblib \
	$(DATA_DIR)/evaluation_metrics.json \
	$(DATA_DIR)/metadata.json

generate:
	mkdir -p "$(DATA_DIR)"
	docker compose run --rm -v "$(abspath $(DATA_DIR)):/data" pipeline

ensure-artifacts:
	@if [ -z "$(filter-out $(wildcard $(ARTIFACTS)),$(ARTIFACTS))" ]; then \
		echo "SignalWatch analytics artifacts are ready."; \
	else \
		echo "Analytics artifacts are missing; generating the deterministic demo dataset..."; \
		$(MAKE) generate DATA_DIR="$(DATA_DIR)"; \
	fi

demo: ensure-artifacts
	docker compose up --build

test:
	docker compose run --rm api uv run pytest
	docker compose run --rm web npm test -- --run

build:
	docker compose --profile pipeline build

smoke:
	./scripts/smoke-test.sh

figures:
	cd backend && MPLBACKEND=Agg uv run --with matplotlib python ../scripts/make_figures.py "$(abspath $(DATA_DIR))"

down:
	docker compose down --remove-orphans
