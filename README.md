# c4sb-demo

This project provides demonstrations and tools for working with and validating linked data graphs, focusing on building-related data models and standards. It includes examples and scripts for graph validation against SHACL shapes for standards such as ASHRAE 223, Brick, and REC.

## Overview

This project, `c4sb-demo`, is a Python application designed to showcase and facilitate the use of semantic web technologies in the building industry. The primary goals of the demonstrations included are:

-   To illustrate how to represent building data using RDF and ontologies like Brick and ASHRAE 223.
-   To provide tools for validating these data graphs against predefined SHACL shapes, ensuring data quality and conformance to standards.
-   To offer practical examples of SPARQL queries for extracting meaningful information from building data graphs.

The project includes sample data files and validation scripts to help users understand and implement these concepts.

## Requirements

-   Python >=3.13

## Installation

### Using pip (Traditional)

1.  **Clone the repository (if you haven't already):**

    ```bash
    git clone <your-repository-url>
    cd c4sb-demo
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\\Scripts\\activate`, for fish shell use `.venv/bin/activate.fish`
    ```

3.  **Install the project and its dependencies:**

    ```bash
    pip install .
    ```

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer and resolver, written in Rust, and designed as a drop-in replacement for `pip` and `pip-tools` workflows.

1.  **Clone the repository (if you haven't already):**

    ```bash
    git clone <your-repository-url>
    cd c4sb-demo
    ```

2.  **Create a virtual environment:**

    ```bash
    uv venv
    source .venv/bin/activate.fish # On Windows use `.venv\\Scripts\\activate`, for bash/zsh use `source .venv/bin/activate`
    ```

3.  **Install the project and its dependencies:**

    ```bash
    uv pip install .
    ```

## Usage

This project provides the following command-line scripts:

-   `c4sb-demo`: Main entry point for the application.

    ```bash
    c4sb-demo
    ```

-   `c4sb-validate`: Script for validating graphs.

    ```bash
    c4sb-validate
    ```

## Development

To install development dependencies (like `pytest` and `watchdog`):

Using pip:

```bash
pip install .[dev]
```

Using uv:

```bash
uv pip install .[dev]
```