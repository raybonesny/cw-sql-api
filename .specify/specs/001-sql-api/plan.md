# Implementation Plan: Secure ConnectWise Manage SQL API Service

**Branch**: `[001-secure-sql-api]` | **Date**: 2026-05-21 | **Spec**: `.specify/specs/001-sql-api/secure-sql-api.spec`

**Input**: Feature specification from `/specs/001-sql-api/secure-sql-api.spec`

## Summary

Build a FastAPI-based secure SQL API service that allows a Copilot agent to query ConnectWise Manage data through structured query requests. The service will accept only validated, parsed query payloads, translate them into parameterized SQL Server SELECT statements, enforce row and execution time limits, authenticate callers with bearer tokens, and log query metadata and responses for auditing.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI, SQLAlchemy, pyodbc, Pydantic, Uvicorn

**Storage**: SQL Server (ConnectWise Manage)

**Testing**: pytest + HTTPX or similar API integration tests

**Target Platform**: Azure Container Apps on Linux container

**Project Type**: web-service / API

**Performance Goals**: Enforce row limit of 500 and execution timeout of 10 seconds; fast fail on invalid requests.

**Constraints**: Read-only SELECT only, no raw SQL input, strict identifier validation, private SQL network access, bearer token auth.

**Scale/Scope**: Single API service for agent-driven SQL queries against a production ConnectWise Manage database.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Read-only first: only structured SELECT queries are permitted.
- Query validation required: all request input must be validated before SQL generation.
- No raw SQL input: clients submit a structured payload, not SQL text.
- Parameterization enforced: all bound values must use query parameters.
- Security & injection protection: identifiers and values are validated and sanitized.
- Observability & audit logging: requests, execution metadata, and response metrics are logged.
- Data protection: sensitive database fields are restricted via allowed table/column lists.
- Network security: SQL Server access is limited to secure VNet/private network paths.

## Project Structure

```text
app/
├── __init__.py
├── auth.py
├── config.py
├── database.py
└── main.py

Dockerfile
requirements.txt
azure-containerapp-template.yaml
README.md

.specify/specs/001-sql-api/
├── secure-sql-api.spec
└── plan.md
```

**Structure Decision**: A single Python web-service project with a dedicated `app/` package and container deployment assets. The feature is implemented in one API service repository without separate frontend or multi-project boundaries.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
