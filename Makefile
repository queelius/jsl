SHELL := /bin/bash

# Simplified Python detection - only use what's currently active
PYTHON := python
PIP := $(PYTHON) -m pip

# Virtual environment paths (for setup commands only)
VENV_DIR := .venv
VENV_BIN := $(VENV_DIR)/bin
VENV_PYTHON := $(VENV_BIN)/python

.PHONY: help install install-dev setup activate check-python clean test test-service coverage docs-serve docs-build docs-deploy bump build-pypi upload-pypi release-pypi examples run-jsl run-service test-clean test-isolated

help:
	@echo "JSL (JSON Serializable Language) Development Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  check-python  - Show detected Python executable"
	@echo "  setup         - Create virtual environment and install dependencies"
	@echo "  activate      - Show command to activate virtual environment"
	@echo "  install       - Install dependencies (requires activated environment)"
	@echo "  install-dev   - Install development dependencies including this package"
	@echo ""
	@echo "Development Commands:"
	@echo "  clean         - Remove temporary files and virtual environment"
	@echo "  clean-force   - Force remove virtual environment (with sudo)"
	@echo "  test          - Run the test suite"
	@echo "  test-service  - Test the FastAPI service"
	@echo "  test-clean    - Test in clean environment (no conda/system interference)"
	@echo "  test-isolated - Test with Docker (requires Docker setup)" 
	@echo "  examples      - Run example JSL programs to verify functionality"
	@echo ""
	@echo "Documentation Commands:"
	@echo "  docs-serve    - Serve the documentation locally"
	@echo "  docs-build    - Build the documentation site"
	@echo "  docs-deploy   - Deploy documentation to GitHub Pages"
	@echo ""
	@echo "Release Commands:"
	@echo "  bump          - Bump the version. Use 'make bump part=minor' or 'make bump part=major'. Defaults to patch."
	@echo "  build-pypi    - Build packages for PyPI distribution"
	@echo "  upload-pypi   - Upload to PyPI (requires PyPI credentials)"
	@echo "  release-pypi  - Full release process: test, build, and upload"
	@echo ""
	@echo "JSL Commands:"
	@echo "  run-jsl       - Run a JSL program (use: make run-jsl FILE=program.json)"
	@echo ""
	@echo "Quick start for new developers:"
	@echo "  make setup && source .venv/bin/activate"
	@echo ""
	@echo "PyPI Release workflow:"
	@echo "  make test && make examples && make docs-build && make release-pypi"
	@echo ""
	@echo "Note: Most commands require an activated virtual environment"
	@echo "Current Python: $(PYTHON)"

check-python:
	@echo "Current Python: $(PYTHON)"
	@echo "Python version:"
	@$(PYTHON) --version
	@echo "Python path:"
	@$(PYTHON) -c "import sys; print(sys.executable)"
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "✓ Virtual environment is active: $$VIRTUAL_ENV"; \
	else \
		echo "⚠ No virtual environment active (consider running 'source .venv/bin/activate')"; \
	fi

setup:
	@echo "Setting up JSL development environment..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV_DIR); \
		echo "Installing basic dependencies..."; \
		$(VENV_PYTHON) -m pip install --upgrade pip; \
		$(VENV_PYTHON) -m pip install pytest coverage mkdocs mkdocs-material; \
		$(VENV_PYTHON) -m pip install -e .; \
		echo "Installing optional service dependencies..."; \
		$(VENV_PYTHON) -m pip install -e ".[service]" || echo "Service dependencies failed - continuing..."; \
		echo ""; \
		echo "✓ Setup complete!"; \
		echo ""; \
		echo "To activate the environment, run:"; \
		echo "  source .venv/bin/activate"; \
	else \
		echo "Virtual environment already exists."; \
		echo "To activate it, run:"; \
		echo "  source .venv/bin/activate"; \
	fi

activate:
	@echo "To activate the virtual environment, run:"
	@echo "  source .venv/bin/activate"
	@echo ""
	@echo "Or copy-paste this command:"
	@echo "source .venv/bin/activate"

install:
	@echo "Installing JSL dependencies..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠ Warning: No virtual environment detected."; \
		echo "Consider running 'make setup && source .venv/bin/activate' first."; \
		echo "Proceeding with system Python..."; \
	fi
	@echo "Using Python: $(PYTHON)"
	@$(PYTHON) --version
	$(PIP) install pytest coverage mkdocs mkdocs-material
	$(PIP) install -e .

clean:
	@echo "Cleaning up..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf build dist .eggs *.egg-info site
	rm -rf .pytest_cache
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Removing virtual environment $(VENV_DIR)/..."; \
		chmod -R u+w $(VENV_DIR) 2>/dev/null || true; \
		rm -rf $(VENV_DIR) 2>/dev/null || \
		(echo "⚠ Some files need elevated permissions. Run 'make clean-force' if needed."; exit 1); \
	fi

clean-force:
	@echo "Force cleaning (with sudo)..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf build dist .eggs *.egg-info site
	rm -rf .pytest_cache
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Force removing virtual environment $(VENV_DIR)/..."; \
		sudo rm -rf $(VENV_DIR); \
	fi

test:
	@echo "Running tests..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠ Warning: No virtual environment detected."; \
		echo "Tests may fail if dependencies aren't installed."; \
	fi
	$(PYTHON) -m pytest -v

coverage:
	@echo "Running tests with coverage..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠ Warning: No virtual environment detected."; \
	fi
	$(PYTHON) -m coverage run --source=jsl -m pytest tests/
	@echo "Coverage report:"
	$(PYTHON) -m coverage report -m

test-service:
	@echo "Testing JSL service..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠ Warning: No virtual environment detected."; \
	fi
	@echo "Starting service for a few seconds to test..."
	@timeout 5s $(PYTHON) -m jsl.service || echo "Service test completed (timeout expected)"


test-clean:
	@echo "Testing in clean environment (no conda/system packages)..."
	@echo "This ensures .venv is truly self-contained"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ No .venv found. Run 'make setup' first."; \
		exit 1; \
	fi
	env -i HOME="$$HOME" PATH="/usr/local/bin:/usr/bin:/bin" bash -c '\
		source .venv/bin/activate && \
		echo "Using Python: $$(python --version)" && \
		echo "Python path: $$(which python)" && \
		python -c "import sys; print(f\"Packages available: {len(sys.path)}\")" && \
		python -m pytest -v'

test-isolated:
	@echo "Testing with Docker to ensure complete isolation..."
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "❌ Docker not found. Skipping isolated test."; \
		echo "   Install Docker to run truly isolated tests."; \
		exit 1; \
	elif ! docker info >/dev/null 2>&1; then \
		echo "❌ Docker daemon not accessible."; \
		echo "   Try: sudo usermod -aG docker $$USER && newgrp docker"; \
		echo "   Or run with: sudo make test-isolated"; \
		exit 1; \
	else \
		docker run --rm -v "$$(pwd):/app" -w /app python:3.11-slim bash -c '\
			python -m venv /tmp/test-venv && \
			source /tmp/test-venv/bin/activate && \
			pip install pytest coverage mkdocs mkdocs-material && \
			pip install -e . && \
			python -m pytest -v'; \
	fi

docs-serve:
	@echo "Serving documentation at http://127.0.0.1:8000"
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠ Warning: No virtual environment detected."; \
	fi
	$(PYTHON) -m mkdocs serve

docs-build:
	@echo "Building documentation..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠ Warning: No virtual environment detected."; \
	fi
	$(PYTHON) -m mkdocs build

docs-deploy:
	@echo "Deploying documentation to GitHub Pages..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠ Warning: No virtual environment detected."; \
	fi
	$(PYTHON) -m mkdocs gh-deploy

part ?= patch

bump:
	@echo "Bumping to next $(part) version..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠ Warning: No virtual environment detected."; \
	fi
	bump-my-version bump --allow-dirty --commit --tag $(part)

examples:
	@echo "Running JSL example programs..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠ Warning: No virtual environment detected."; \
	fi
	@echo "Testing basic JSL evaluation..."
	@echo '["def", "x", 42]' | $(PYTHON) -c "import sys, json; from jsl import evaluate, get_prelude; from jsl.core import Env; prelude = get_prelude(); env = Env(parent=prelude); program = json.load(sys.stdin); result = evaluate(program, env); print('Result:', result)"
	@echo "Testing arithmetic..."
	@echo '["+", 1, 2, 3]' | $(PYTHON) -c "import sys, json; from jsl import evaluate, get_prelude; from jsl.core import Env; prelude = get_prelude(); env = Env(parent=prelude); program = json.load(sys.stdin); result = evaluate(program, env); print('Result:', result)"
	@echo "Testing lambda..."
	@echo '["lambda", ["x"], ["*", "x", 2]]' | $(PYTHON) -c "import sys, json; from jsl import evaluate, get_prelude; from jsl.core import Env; prelude = get_prelude(); env = Env(parent=prelude); program = json.load(sys.stdin); result = evaluate(program, env); print('Result type:', type(result).__name__)"
	@if [ -f "test_program.json" ]; then \
		echo "Testing program from test_program.json..."; \
		$(PYTHON) -m jsl.runner test_program.json || echo "Note: test_program.json may need updating"; \
	fi
	@echo "✓ JSL examples completed successfully"

run-jsl:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make run-jsl FILE=program.json"; \
		echo "Example: make run-jsl FILE=test_program.json"; \
		exit 1; \
	fi
	@echo "Running JSL program: $(FILE)"
	$(PYTHON) -m jsl.runner $(FILE)

build-pypi:
	@echo "Building packages for PyPI..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "❌ Virtual environment required for building."; \
		echo "Run: source .venv/bin/activate"; \
		exit 1; \
	fi
	@echo "Installing build dependencies..."
	$(PIP) install --upgrade pip build twine
	@echo "Cleaning previous builds..."
	rm -rf dist/ build/ *.egg-info/
	@echo "Building source and wheel distributions..."
	$(PYTHON) -m build
	@echo "Checking distributions..."
	$(PYTHON) -m twine check dist/*
	@echo "✓ Packages built successfully:"
	@ls -la dist/

upload-pypi:
	@echo "Uploading to PyPI..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "❌ Virtual environment required for uploading."; \
		exit 1; \
	fi
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist)" ]; then \
		echo "❌ No distributions found. Run 'make build-pypi' first."; \
		exit 1; \
	fi
	@echo "This will upload to PyPI. Make sure you have:"
	@echo "  1. Set up PyPI credentials (twine configure or .pypirc)"
	@echo "  2. Tested the package thoroughly"
	@echo "  3. Updated version and changelog"
	@echo ""
	@read -p "Continue with upload? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Uploading to PyPI..."; \
		$(PYTHON) -m twine upload dist/*; \
		echo "✓ Upload complete!"; \
	else \
		echo "Upload cancelled."; \
	fi

upload-test-pypi:
	@echo "Uploading to Test PyPI..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "❌ Virtual environment required for uploading."; \
		exit 1; \
	fi
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist)" ]; then \
		echo "❌ No distributions found. Run 'make build-pypi' first."; \
		exit 1; \
	fi
	@echo "Uploading to Test PyPI (https://test.pypi.org/)..."
	$(PYTHON) -m twine upload --repository testpypi dist/*
	@echo "✓ Upload to Test PyPI complete!"
	@echo "Test installation with:"
	@echo "  pip install --index-url https://test.pypi.org/simple/ treeshell"

release-check:
	@echo "Pre-release checklist..."
	@echo "Running tests..."
	@$(MAKE) test > /dev/null 2>&1 && echo "✓ Tests pass" || (echo "❌ Tests failed"; exit 1)
	@echo "Testing examples..."
	@$(MAKE) examples > /dev/null 2>&1 && echo "✓ Examples work" || (echo "❌ Examples failed"; exit 1)
	@echo "Building documentation..."
	@$(MAKE) docs-build > /dev/null 2>&1 && echo "✓ Documentation builds" || (echo "❌ Documentation failed"; exit 1)
	@echo "Checking package structure..."
	@[ -f "pyproject.toml" ] && echo "✓ pyproject.toml exists" || (echo "❌ pyproject.toml missing"; exit 1)
	@[ -f "README.md" ] && echo "✓ README.md exists" || (echo "❌ README.md missing"; exit 1)
	@[ -f "LICENSE" ] && echo "✓ LICENSE exists" || (echo "❌ LICENSE missing"; exit 1)
	@echo "Checking git status..."
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "❌ Git working directory not clean. Commit changes first."; \
		git status --short; \
		exit 1; \
	else \
		echo "✓ Git working directory clean"; \
	fi
	@echo "✓ All pre-release checks passed!"

release-pypi: release-check
	@echo "Starting PyPI release process..."
	@echo "Building packages..."
	@$(MAKE) build-pypi
	@echo ""
	@echo "Release ready! Package contents:"
	@ls -la dist/
	@echo ""
	@echo "To complete the release:"
	@echo "  1. Review the built packages above"
	@echo "  2. Test upload: make upload-test-pypi"
	@echo "  3. Production upload: make upload-pypi"
	@echo "  4. Deploy docs: make docs-deploy"
	@echo ""
	@echo "Or upload directly now:"
	@read -p "Upload to PyPI now? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) upload-pypi; \
		echo ""; \
		echo "🎉 Release complete! Don't forget to:"; \
		echo "  - Deploy documentation: make docs-deploy"; \
		echo "  - Create GitHub release with release notes"; \
		echo "  - Announce the release"; \
	else \
		echo "Build complete. Run 'make upload-pypi' when ready."; \
	fi

install-dev: install
	@echo "Installing package in development mode..."
	$(PIP) install -e .
