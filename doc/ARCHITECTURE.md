# Architecture Overview

## Core Modules (`src/`)
- `csv_reporter.py` – main reporting engine (generic)
- `csv_reporter_config.py` – loads/manages queries + csv configs
- `language_catalog.py` / `language_service.py` – domain-aware language/text handling
- `sqlite_adapter.py` – DB adapter for SQLite (Oracle adapter planned)

## Configuration (`config/`)
- `queries.json` – SQL statements per label
- `csv_configs.json` – CSV formatting rules
- `messages.json` – language messages with domain/context

## REST API (`server/app/`)
- `main.py` – FastAPI entrypoint
- `settings.py` – environment-driven configuration
- `lifecycle.py` – startup/shutdown hooks (load language, configs, DB)
- `deps.py` – shared dependencies for routers
- `routers/` – endpoints (health, config, csv, admin)
- `services/` – thin service layer (CsvService etc.)

## Examples (`examples/`)
- Scripts to init SQLite DB and run local reporter tests.

## Tests (`tests/`)
- Smoke + integration tests (pytest).