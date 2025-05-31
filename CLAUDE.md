# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test/Lint Commands

```bash
# Install the package in development mode
pip install -e .

# Install development dependencies 
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test
pytest tests/test_sparql_queries.py::test_query_1_results

# Lint code
ruff check .

# Format code
ruff format .

# Validate graphs against SHACL constraints
python -m c4sb_demo.validate_graphs
```

## Code Style Guidelines

- **Type Hints**: Use Python type hints for all functions (see validate_graphs.py)
- **Path Handling**: Use pathlib.Path for file paths
- **Error Handling**: Use try/except blocks with specific exceptions
- **Docstrings**: Include docstrings for functions and modules
- **Imports**: Group imports by standard library, third-party, and local
- **Naming**: Use snake_case for variables/functions, PascalCase for classes
- **Testing**: Write pytest-based tests for all functionality