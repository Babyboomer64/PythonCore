# PythonCore

[![CI](https://github.com/Babyboomer64/PythonCore/actions/workflows/ci.yml/badge.svg)](https://github.com/Babyboomer64/PythonCore/actions/workflows/ci.yml)

Core Python Modules

## Project Overview

This repository contains reusable Python core modules and a demo REST API service ("Tweight API").  
The goals are:
- Provide a clean foundation for CSV reporting with flexible DB adapters (e.g. Oracle, SQLite).
- Centralize language and configuration management (JSON-driven, domain-aware).
- Offer an extendable FastAPI-based service template for future applications.

## Project Structure

- `src/` – Core modules (CSV reporter, config, language, adapters).  
- `config/` – JSON files for queries, CSV configurations, and messages.  
- `examples/` – Example scripts to initialize test DB and run exports.  
- `server/` – FastAPI service ("Tweight API") with routers and lifecycle logic.  
- `tests/` – Smoke tests that run the examples.  

## Next Steps

- Extend the `/csv` router to execute exports via REST.  
- Add background job support for long-running exports.  
- Expand admin endpoints (reload configs, service info, version).  
- Harden error handling and logging for production use.  

## Quickstart
```bash
python examples/init_sqlite_db.py
python examples/test_language_catalog.py
python examples/test_csv_reporter.py ALL_CUSTOMERS NDL_STRICT out.csv
```

## Tweight API Service

### 1. Environment vorbereiten
```bash
source activate_dev.sh
```

### 2. Dependencies (einmalig im venv)
```bash
python -m pip install fastapi "uvicorn[standard]" pydantic pydantic-settings
```

### 3. Service starten
```bash
# mit Admin-Token (für Shutdown)
export ADMIN_TOKEN="supersecret123"
uvicorn app.main:app --app-dir server --reload
```

Der Service läuft dann unter:  
👉 http://127.0.0.1:8000

### 4. Test-Endpunkte
- Liveness: http://127.0.0.1:8000/health/live  
- Readiness: http://127.0.0.1:8000/health/ready  
- Queries-Katalog: http://127.0.0.1:8000/config/queries  
- CSV-Configs-Katalog: http://127.0.0.1:8000/config/csv-configs  
- Swagger UI: http://127.0.0.1:8000/docs  

### 5. Service herunterfahren

**Swagger UI**  
- `POST /admin/shutdown` auswählen  
- „Try it out“ → Header `X-Admin-Token` setzen → „Execute“  

**Terminal**  
```bash
curl -X POST http://127.0.0.1:8000/admin/shutdown \
  -H "X-Admin-Token: supersecret123"
```
Antwort:
```json
{"status": "shutting down"}
```
