SHELL := /bin/bash

# Python detection - use what's currently active
PYTHON := python
PIP := $(PYTHON) -m pip

# Virtual environment paths
VENV_DIR := .venv
VENV_BIN := $(VENV_DIR)/bin
VENV_PYTHON := $(VENV_BIN)/python

.PHONY: help install install-dev setup activate check-python clean test coverage docs bump build upload release examples run-jsl

help:
	@echo "JSL (JSON Serializable Language) Development Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  check-python  - Show detected Python executable and environment"
	@echo "  setup         - Create virtual environment and install dependencies"
	@echo "  activate      - Show command to activate virtual environment"
	@echo "  install       - Install runtime dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo ""
	@echo "Development Commands:"
	@echo "  clean         - Remove temporary files and virtual environment"
	@echo "  test          - Run all tests (with coverage by default)"
	@echo "  test-only     - Run tests without coverage"
	@echo "  test-runner   - Run only runner module tests"
	@echo "  test-fluent   - Run only fluent API tests"
	@echo "  test-file     - Run specific test file or function (see usage below)"
	@echo "  test-clean    - Test in isolated environment"
	@echo "  examples      - Run example JSL programs"
	@echo ""
	@echo "Documentation Commands:"
	@echo "  docs          - Build and serve documentation locally"
	@echo "  docs-build    - Build documentation only"
	@echo "  docs-deploy   - Deploy documentation to GitHub Pages"
	@echo ""
	@echo "Release Commands:"
	@echo "  bump          - Bump version (use: make bump PART=minor|major, default=patch)"
	@echo "  build         - Build packages for PyPI"
	@echo "  upload        - Upload to PyPI (interactive)"
	@echo "  upload-test   - Upload to Test PyPI"
	@echo "  release       - Full release: test, build, upload"
	@echo ""
	@echo "JSL Commands:"
	@echo "  run-jsl       - Run JSL program (use: make run-jsl FILE=program.json)"
	@echo ""
	@echo "Test Examples:"
	@echo "  make test-file TEST_FILE=test_runner.py"
	@echo "  make test-file TEST_FILE=test_fluent.py TEST_FUNC=test_arithmetic_operators"
	@echo "  make test-file TEST_FILE=tests/test_runner.py TEST_FUNC=TestJSLRunner::test_execute_basic_arithmetic"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make setup && source .venv/bin/activate  # First time setup"
	@echo "  make test                                # Run tests"
	@echo "  make docs                                # View documentation"
	@echo "  make release                             # Release to PyPI"

check-python:
	@echo "Python Environment Status:"
	@echo "Current Python: $(PYTHON)"
	@echo "Python version: $$($(PYTHON) --version)"
	@echo "Python path: $$($(PYTHON) -c 'import sys; print(sys.executable)')"
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "✓ Virtual environment active: $$VIRTUAL_ENV"; \
	else \
		echo "⚠ No virtual environment active"; \
		if [ -d "$(VENV_DIR)" ]; then \
			echo "  Run: source .venv/bin/activate"; \
		else \
			echo "  Run: make setup"; \
		fi \
	fi

setup:
	@echo "Setting up JSL development environment..."
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment already exists at $(VENV_DIR)"; \
		echo "To recreate, run: make clean && make setup"; \
		echo "To activate, run: source .venv/bin/activate"; \
		exit 0; \
	fi
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV_DIR)
	@echo "Installing dependencies..."
	$(VENV_PYTHON) -m pip install --upgrade pip setuptools wheel
	$(VENV_PYTHON) -m pip install -e ".[dev]" || \
		(echo "Installing fallback dependencies..." && \
		 $(VENV_PYTHON) -m pip install pytest coverage mkdocs mkdocs-material && \
		 $(VENV_PYTHON) -m pip install -e .)
	@echo ""
	@echo "✓ Setup complete!"
	@echo "To activate: source .venv/bin/activate"

activate:
	@echo "To activate the virtual environment:"
	@echo "  source .venv/bin/activate"

install:
	@echo "Installing JSL runtime dependencies..."
	@$(MAKE) --no-print-directory _check-env
	$(PIP) install -e .

install-dev:
	@echo "Installing JSL development dependencies..."
	@$(MAKE) --no-print-directory _check-env
	$(PIP) install -e ".[dev]" || \
		(echo "Installing individual dev dependencies..." && \
		 $(PIP) install pytest coverage mkdocs mkdocs-material build twine bump-my-version && \
		 $(PIP) install -e .)

clean:
	@echo "Cleaning up..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf build/ dist/ .eggs/ *.egg-info/ site/ .pytest_cache/ .coverage htmlcov/
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Removing virtual environment..."; \
		chmod -R u+w $(VENV_DIR) 2>/dev/null || true; \
		rm -rf $(VENV_DIR) || \
		 (echo "⚠ Permission issue. Try: sudo rm -rf $(VENV_DIR)"; exit 1); \
	fi

# Test commands - unified approach
test:
	@echo "Running tests with coverage..."
	@$(MAKE) --no-print-directory _check-env
	$(PYTHON) -m pytest tests/ -v --cov=jsl --cov-report=term --cov-report=html

test-only:
	@echo "Running tests without coverage..."
	@$(MAKE) --no-print-directory _check-env
	$(PYTHON) -m pytest tests/ -v

test-runner:
	@echo "Running runner module tests..."
	@$(MAKE) --no-print-directory _check-env
	$(PYTHON) -m pytest tests/test_runner.py -v

test-fluent:
	@echo "Running fluent API tests..."
	@$(MAKE) --no-print-directory _check-env
	$(PYTHON) -m pytest tests/test_fluent.py -v

# New flexible test target for individual files/functions
TEST_FILE ?=
TEST_FUNC ?=
test-file:
	@if [ -z "$(TEST_FILE)" ]; then \
		echo "Usage: make test-file TEST_FILE=test_filename [TEST_FUNC=test_function]"; \
		echo "Examples:"; \
		echo "  make test-file TEST_FILE=test_runner.py"; \
		echo "  make test-file TEST_FILE=test_fluent.py TEST_FUNC=test_arithmetic_operators"; \
		echo "  make test-file TEST_FILE=tests/test_runner.py TEST_FUNC=TestJSLRunner::test_execute_basic_arithmetic"; \
		exit 1; \
	fi
	@$(MAKE) --no-print-directory _check-env
	@if [ -n "$(TEST_FUNC)" ]; then \
		echo "Running specific test: $(TEST_FILE)::$(TEST_FUNC)"; \
		$(PYTHON) -m pytest "$(TEST_FILE)::$(TEST_FUNC)" -v; \
	else \
		echo "Running test file: $(TEST_FILE)"; \
		$(PYTHON) -m pytest "$(TEST_FILE)" -v; \
	fi

test-clean:
	@echo "Testing in clean environment..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ No .venv found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "Testing with isolated environment (no system packages)..."
	env -i HOME="$$HOME" PATH="/usr/local/bin:/usr/bin:/bin" bash -c '\
		source .venv/bin/activate && \
		echo "Using: $$(python --version) at $$(which python)" && \
		python -m pytest tests/ -v'

# Coverage alias for backwards compatibility
coverage: test

# Documentation commands - unified
docs:
	@echo "Building and serving documentation..."
	@$(MAKE) --no-print-directory _check-env
	@$(MAKE) --no-print-directory docs-build
	@echo "Serving at http://127.0.0.1:8000 (Ctrl+C to stop)"
	$(PYTHON) -m mkdocs serve

docs-build:
	@echo "Building documentation..."
	@$(MAKE) --no-print-directory _check-env
	$(PYTHON) -m mkdocs build

docs-deploy:
	@echo "Deploying documentation to GitHub Pages..."
	@$(MAKE) --no-print-directory _check-env
	$(PYTHON) -m mkdocs gh-deploy

# Version management
PART ?= patch
bump:
	@echo "Bumping $(PART) version..."
	@$(MAKE) --no-print-directory _check-env
	@if ! command -v bump-my-version >/dev/null 2>&1; then \
		echo "Installing bump-my-version..."; \
		$(PIP) install bump-my-version; \
	fi
	bump-my-version bump --allow-dirty --commit --tag $(PART)

# Build and release - unified approach
build:
	@echo "Building packages for PyPI..."
	@$(MAKE) --no-print-directory _check-env
	@$(MAKE) --no-print-directory _install-build-deps
	@echo "Cleaning previous builds..."
	rm -rf dist/ build/ *.egg-info/
	@echo "Building distributions..."
	$(PYTHON) -m build
	@echo "Checking distributions..."
	$(PYTHON) -m twine check dist/*
	@echo "✓ Built packages:"
	@ls -la dist/

upload:
	@echo "Uploading to PyPI..."
	@$(MAKE) --no-print-directory _check-env
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist 2>/dev/null)" ]; then \
		echo "❌ No distributions found. Run 'make build' first."; \
		exit 1; \
	fi
	@echo "This will upload to production PyPI."
	@echo "Packages to upload:"
	@ls -la dist/
	@echo ""
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(PYTHON) -m twine upload dist/*; \
		echo "✓ Upload complete!"; \
	else \
		echo "Upload cancelled."; \
	fi

upload-test:
	@echo "Uploading to Test PyPI..."
	@$(MAKE) --no-print-directory _check-env
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist 2>/dev/null)" ]; then \
		echo "❌ No distributions found. Run 'make build' first."; \
		exit 1; \
	fi
	$(PYTHON) -m twine upload --repository testpypi dist/*
	@echo "✓ Uploaded to Test PyPI!"
	@echo "Test install: pip install --index-url https://test.pypi.org/simple/ jsl"

release:
	@echo "Starting release process..."
	@$(MAKE) --no-print-directory _pre-release-checks
	@$(MAKE) build
	@echo ""
	@echo "🚀 Release ready!"
	@echo "Next steps:"
	@echo "  1. Test upload: make upload-test"
	@echo "  2. Production upload: make upload"
	@echo "  3. Deploy docs: make docs-deploy"
	@echo ""
	@read -p "Upload to PyPI now? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) upload; \
		echo ""; \
		echo "🎉 Release complete!"; \
		echo "Don't forget: make docs-deploy"; \
	fi

# JSL execution
examples:
	@echo "Running JSL examples..."
	@$(MAKE) --no-print-directory _check-env
	@echo "1. Testing basic arithmetic..."
	@echo '["+", 1, 2, 3]' | $(PYTHON) -c "import sys,json; from jsl import evaluate, get_prelude; result = evaluate(json.load(sys.stdin), get_prelude()); print('Result:', result)"
	@echo "2. Testing variable definition..."
	@echo '["def", "x", 42]' | $(PYTHON) -c "import sys,json; from jsl import evaluate, get_prelude; from jsl.core import Env; env = Env(parent=get_prelude()); evaluate(json.load(sys.stdin), env); print('Variable x:', env.get('x'))"
	@echo "3. Testing lambda functions..."
	@echo '[["lambda", ["x"], ["*", "x", 2]], 5]' | $(PYTHON) -c "import sys,json; from jsl import evaluate, get_prelude; result = evaluate(json.load(sys.stdin), get_prelude()); print('Result:', result)"
	@echo "4. Testing runner module..."
	@$(PYTHON) -c "from jsl.runner import JSLRunner; r = JSLRunner(); print('Runner test:', r.execute(['+', 10, 20, 30]))"
	@echo "5. Testing fluent API..."
	@$(PYTHON) -c "from jsl.fluent import E, V; from jsl.runner import JSLRunner; expr = E.add(1,2,3); r = JSLRunner(); print('Fluent test:', r.execute(expr.to_jsl()))"
	@echo "✓ All examples passed!"

run-jsl:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make run-jsl FILE=program.json"; \
		echo "Example: make run-jsl FILE=examples/hello.json"; \
		exit 1; \
	fi
	@$(MAKE) --no-print-directory _check-env
	@echo "Running JSL program: $(FILE)"
	$(PYTHON) -c "import json; from jsl import evaluate, get_prelude; result = evaluate(json.load(open('$(FILE)')), get_prelude()); print('Result:', result)"

# Internal helper targets (not shown in help)
_check-env:
	@if [ -z "$$VIRTUAL_ENV" ] && [ ! -f "$(VENV_DIR)/pyvenv.cfg" ]; then \
		echo "⚠ No virtual environment detected."; \
		echo "Run 'make setup && source .venv/bin/activate' first."; \
	fi

_install-build-deps:
	@if ! $(PYTHON) -c "import build, twine" >/dev/null 2>&1; then \
		echo "Installing build dependencies..."; \
		$(PIP) install build twine; \
	fi

_pre-release-checks:
	@echo "Running pre-release checks..."
	@$(MAKE) --no-print-directory test-only >/dev/null 2>&1 && echo "✓ Tests pass" || (echo "❌ Tests failed"; exit 1)
	@$(MAKE) --no-print-directory examples >/dev/null 2>&1 && echo "✓ Examples work" || (echo "❌ Examples failed"; exit 1)
	@$(MAKE) --no-print-directory docs-build >/dev/null 2>&1 && echo "✓ Documentation builds" || (echo "❌ Documentation failed"; exit 1)
	@[ -f "pyproject.toml" ] && echo "✓ pyproject.toml exists" || (echo "❌ pyproject.toml missing"; exit 1)
	@[ -f "README.md" ] && echo "✓ README.md exists" || (echo "❌ README.md missing"; exit 1)
	@if command -v git >/dev/null 2>&1 && [ -d ".git" ]; then \
		if [ -n "$$(git status --porcelain 2>/dev/null)" ]; then \
			echo "❌ Git working directory not clean"; \
			git status --short; \
			exit 1; \
		else \
			echo "✓ Git working directory clean"; \
		fi \
	fi
	@echo "✓ All pre-release checks passed"
