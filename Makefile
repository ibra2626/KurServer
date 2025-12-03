.PHONY: help install install-dev test test-cov lint format clean docs docs-serve build upload

help:
	@echo "Available commands:"
	@echo "  install      Install the package"
	@echo "  install-dev  Install the package with development dependencies"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  clean        Clean build artifacts"
	@echo "  docs         Build documentation"
	@echo "  docs-serve   Serve documentation locally"
	@echo "  build        Build package"
	@echo "  upload       Upload package to PyPI"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=src/kurserver --cov-report=html --cov-report=term-missing

lint:
	flake8 src tests
	mypy src

format:
	black src tests
	isort src tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf docs/_build/

docs:
	cd docs && make html

docs-serve:
	cd docs/_build/html && python -m http.server 8000

build:
	python -m build

upload:
	python -m twine upload dist/*