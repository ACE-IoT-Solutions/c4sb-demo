# c4sb-demo

Add your description here

## Overview

This project, `c4sb-demo`, is a Python application.

## Requirements

- Python >=3.13

## Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <your-repository-url>
    cd c4sb-demo
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install the project and its dependencies:**
    ```bash
    pip install .
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

To install development dependencies (like `pytest` and `watchdog`), run:
```bash
pip install .[dev]
```