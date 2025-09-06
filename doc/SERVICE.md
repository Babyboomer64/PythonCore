


# Tweight API – Service Guide

## Starting the Service
```bash
source activate_dev.sh
export ADMIN_TOKEN="supersecret123"
uvicorn app.main:app --app-dir server --reload
```

## Endpoints

### Health
- `GET /health/live` – liveness
- `GET /health/ready` – readiness

### Config
- `GET /config/queries` – list query labels
- `GET /config/csv-configs` – list csv config labels

### CSV
- `POST /csv/export` – run a CSV export  
  Body example:
  ```json
  {
    "select_label": "ALL_CUSTOMERS",
    "csv_config_label": "NDL_STRICT",
    "out_path": "out.csv"
  }
  ```

### Admin
- `POST /admin/shutdown` – graceful shutdown (requires `X-Admin-Token` header)

## Documentation
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json