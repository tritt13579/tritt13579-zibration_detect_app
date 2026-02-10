# Zibration Detect App

Desktop application for managing `.pt` models and running Excel detection workflow (UI-first with mock detection).

## Features (Phase 1)

- Import and store PyTorch model files (`.pt`) inside project storage.
- Reuse existing models from a local model library.
- Restore last used model on app startup.
- Select Excel file (`.xlsx`, `.xls`) and load mock preview rows.
- Run mock detection and show results in a table.

## Tech Stack

- Python 3.12+
- PySide6 (Qt for Python)
- Clean-ish layered architecture: UI / application / domain / infrastructure

## Project Structure

```text
src/app/
  config/            # Paths and settings
  domain/            # Entities and protocols
  application/       # Services and controllers
  infrastructure/    # Repositories, gateways, persistence
  ui/                # Main window and widgets
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
source .venv/bin/activate
PYTHONPATH=src python -m app.main
```

## Test

```bash
source .venv/bin/activate
PYTHONPATH=src pytest -q
```

## Notes

- Excel parsing and real model inference are intentionally mocked in this phase.
- Current implementation focuses on maintainable structure and UI/UX flow.
- Next phase can replace `excel_gateway.py` and `detector_gateway.py` with real logic.
