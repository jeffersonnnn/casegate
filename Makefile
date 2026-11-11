.PHONY: install lint type test demo demo-offline baseline

install:
	uv sync --all-extras

lint:
	uv run ruff check
	uv run ruff format --check

type:
	uv run mypy --strict src/casegate

test:
	uv run pytest -q --cov=casegate --cov-fail-under=85

demo:
	uv sync --all-extras && uv run casegate run evals --repeat 1

demo-offline:
	uv sync --all-extras && uv run casegate run tests/fixtures/suite_fake --repeat 1 --fake-judge

# A fresh cache dir so the baseline holds real calls, never cached ones (SPEC 16.3).
baseline:
	CASEGATE_CACHE_DIR=$$(mktemp -d) uv run casegate run evals --repeat 5 --out evals/baseline.json
