IMAGE_NAME ?= yeahdongcn/agentman:base

default: run

.PHONY: build-base-image
build-base-image:
	docker buildx build --platform linux/amd64,linux/arm64 \
		--build-arg NODE_VERSION=22 \
		--tag $(IMAGE_NAME) \
		-f docker/Dockerfile.base \
		--push .

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

.PHONY: test
test:
	uv pip install -e .[test]
	uv run pytest

.PHONY: test-cov
test-cov:
	uv pip install -e .[test]
	uv run pytest --cov=src/agentman --cov-report=term-missing --cov-report=html

.PHONY: test-verbose
test-verbose:
	uv pip install -e .[test]
	uv run pytest -v -s