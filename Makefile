default: run

.PHONY: build
build:
	uv pip install -e .

.PHONY: run
run: build
	uv run agentman

.PHONY: check-format
check-format:
	uv pip install -e .[dev]
	uv run black --check --diff */*/*.py
	uv run isort --check --diff */*/*.py

.PHONY: format
format:
	black */*/*.py
	isort */*/*.py