# Secure ConnectWise Manage SQL API

This repository implements a FastAPI service for structured, read-only SQL queries against a ConnectWise Manage SQL Server database.

## Features

- Structured query endpoint (`POST /api/query`)
- Token-based bearer authentication
- Whitelisted table and column validation
- Parameterized SQL generation to prevent SQL injection
- Read-only `SELECT` queries only
- Execution time and row count limits
- Audit logging for requests and responses
- Azure Container Apps deployment support

## Quick Start

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Set environment variables:

- `API_TOKEN`
- `SQL_SERVER_HOST`
- `SQL_SERVER_DATABASE`
- `SQL_SERVER_USER`
- `SQL_SERVER_PASSWORD`
- `ALLOWED_TABLES_JSON` (optional)

3. Run locally:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Example Request

```http
POST /api/query HTTP/1.1
Authorization: Bearer <API_TOKEN>
Content-Type: application/json

{
  "table": "Contact",
  "columns": ["id", "firstName", "lastName", "email"],
  "filters": [
    {"field": "status", "operator": "eq", "value": "Active"}
  ],
  "order_by": [{"field": "id", "direction": "asc"}],
  "limit": 100
}
```

## Deployment

- Build the container with the provided `Dockerfile`
- Deploy to Azure Container Apps using `azure-containerapp-template.yaml`
- Configure secure network access to the SQL Server through VNet integration or private endpoint

## Notes

- Only tables and columns defined in `ALLOWED_TABLES_JSON` are queryable.
- The service uses `SELECT TOP {limit}` for SQL Server row limiting.
- Authentication is enforced using bearer token validation.
