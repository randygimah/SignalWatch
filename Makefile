.PHONY: generate demo test build down

generate:
	docker compose run --rm pipeline

demo:
	docker compose run --rm pipeline
	docker compose up --build

test:
	docker compose run --rm api uv run pytest
	docker compose run --rm web npm test -- --run

build:
	docker compose build

down:
	docker compose down --remove-orphans

