IMAGE_NAME ?= yeahdongcn/agentman:base

default: run

.PHONY: publish-base-image
publish-base-image:
	docker buildx build --platform linux/amd64,linux/arm64 \
		--build-arg NODE_VERSION=22 \
		--tag $(IMAGE_NAME) \
		-f docker/Dockerfile.base \
		--push .

.PHONY: install
install:
	uv pip install -e .

.PHONY: run
run: install
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

# Publishing targets
.PHONY: build publish-test publish-prod clean-build

build: ## Build the package
	@./scripts/build.sh

publish-test: build ## Publish to TestPyPI
	@./scripts/publish.sh testpypi

publish-prod: build ## Publish to PyPI
	@./scripts/publish.sh pypi

clean-build: ## Clean build artifacts
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf dist/ build/ src/*.egg-info/
	@echo "✅ Build artifacts cleaned"