MAKEFILE_ABS_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

.DEFAULT_GOAL := help

##@ Help
.PHONY: help
help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


.PHONY: all
all: lint test


##@ Environment
.PHONY: env
env: ## Setup development environment
	@uv sync --all-extras --link-mode=copy


.PHONY: clean
clean: ## Clean up build artifacts
	@echo "Cleaning up..."
	@rm -rf dist
	@rm -rf pymarkdoc.egg-info
	@rm -rf .venv/
	@rm -rf .pytest_cache/
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@find . -name "*~" -delete
	@echo "✓ Cleaned up"


##@ Compiling

.PHONY: build
build: ## Build
	@echo "Building..."
	@uv build


##@ Tests

.PHONY: test
test: env ## Run unit tests
	@uv run pytest tests/ -v

.PHONY: test-matrix
test-matrix: env ## Run tests across Python versions with tox
	@uv run tox


##@ Linting / Formatting

.PHONY: lint
lint: env ## Check code style
	@echo "Checking code style..."
	@uv run ruff check pymarkdoc/ tests/

.PHONY: lint-fix
lint-fix: env ## Fix code style issues automatically
	@echo "Fixing code style..."
	@uv run ruff check --fix pymarkdoc/ tests/

.PHONY: format
format: env ## Format code
	@echo "Formatting code..."
	@uv run ruff format pymarkdoc/ tests/


##@ Docs

.PHONY: docs
docs: env ## Build API docs with pdoc
	@uv run pdoc -o docs/api pymarkdoc


##@ Fixtures

.PHONY: fixtures
fixtures: env ## Regenerate Python fixtures (AST + HTML)
	@uv run python scripts/generate_py_fixtures.py

.PHONY: fixtures-js
fixtures-js: env ## Regenerate JS fixtures (requires built Markdoc dist)
	@node tests/js/generate_fixtures.js
