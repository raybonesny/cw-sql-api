# Tasks: Secure ConnectWise Manage SQL API Service

**Input**: Design documents from `/specs/001-sql-api/`

**Prerequisites**: plan.md, secure-sql-api.spec

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Create Python package structure under `app/` with `__init__.py`, `auth.py`, `config.py`, `database.py`, and `main.py`
- [ ] T002 Add dependency manifest `requirements.txt` with FastAPI, Uvicorn, SQLAlchemy, pyodbc, and Pydantic
- [ ] T003 Create `Dockerfile` for containerizing the FastAPI service
- [ ] T004 Create `.dockerignore` to exclude environment files and `.specify` metadata from container builds
- [ ] T005 Add `README.md` documenting local launch, config variables, and sample `/api/query` usage

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T006 [P] Implement environment configuration in `app/config.py` with SQL Server connection settings, query limits, timeout settings, and allowed table/column mapping
- [ ] T007 [P] Implement bearer token authentication in `app/auth.py` and require it for all query endpoint requests
- [ ] T008 [P] Implement structured request/response schemas in `app/schemas.py` for query payloads, filters, order-by, and JSON result shape
- [ ] T009 [P] Implement SQL Server connection creation in `app/database.py` using SQLAlchemy and pyodbc
- [ ] T010 [P] Implement logging setup in `app/main.py` and ensure query request metadata can be captured for auditing
- [ ] T011 Implement a health check endpoint in `app/main.py` for container readiness

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 - Structured read-only SQL access for Copilot (Priority: P1) 🎯 MVP

**Goal**: Allow Copilot to submit structured query requests and return sanitized SELECT results as JSON.

**Independent Test**: POST `/api/query` with a valid structured payload and verify `200 OK` with `rows`, `columns`, and `row_count`.

### Implementation

- [ ] T012 [US1] Implement `QueryRequest` validation rules in `app/schemas.py` to require `table`, optional `columns`, `filters`, `order_by`, and `limit`
- [ ] T013 [US1] Implement `build_select_query()` in `app/database.py` to convert request payloads into a parameterized `SELECT TOP {limit}` statement
- [ ] T014 [US1] Implement column and table whitelist enforcement in `app/database.py` using allowed table/column mapping
- [ ] T015 [US1] Implement safe filter translation for operators `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `contains`, `startswith`, `endswith`
- [ ] T016 [US1] Implement `POST /api/query` in `app/main.py` and return `QueryResponse` with execution metadata

### Tests

- [ ] T017 [P] [US1] Add integration test `tests/integration/test_query_api.py` for a successful structured query path
- [ ] T018 [P] [US1] Add validation test `tests/unit/test_schemas.py` for invalid column/table payloads

---

## Phase 4: User Story 2 - Enforce authentication before execution (Priority: P1)

**Goal**: Ensure only authenticated clients can execute SQL queries.

**Independent Test**: Send `/api/query` without a bearer token and verify `401 Unauthorized`.

### Implementation

- [ ] T019 [US2] Add HTTP Bearer auth dependency to `app/main.py` using `app/auth.py`
- [ ] T020 [US2] Validate the bearer token against `API_TOKEN` in `app/config.py`
- [ ] T021 [US2] Ensure unauthorized requests fail before any query execution

### Tests

- [ ] T022 [P] [US2] Add integration test for missing/invalid bearer token in `tests/integration/test_auth.py`

---

## Phase 5: User Story 3 - Audit logging and query limits (Priority: P2)

**Goal**: Log every query and enforce row count and execution time limits.

**Independent Test**: Query and inspect logs for request metadata, and confirm overly large or slow queries are rejected.

### Implementation

- [ ] T023 [US3] Add request/response audit logging in `app/main.py` for subject, table, row count, and execution time
- [ ] T024 [US3] Enforce `QUERY_ROW_LIMIT` and `MAX_EXECUTION_TIME_SECONDS` in `app/database.py`
- [ ] T025 [US3] Return `429 Too Many Requests` for row-limit or execution-time violations and `400 Bad Request` for validation issues
- [ ] T026 [US3] Log query errors without exposing internal SQL/database details

### Tests

- [ ] T027 [P] [US3] Add integration test for row-limit enforcement in `tests/integration/test_limits.py`
- [ ] T028 [P] [US3] Add integration test for execution-time limit behavior in `tests/integration/test_limits.py`

---

## Phase 6: Deployment & Security Hardening

- [ ] T029 Create `azure-containerapp-template.yaml` with container app configuration, environment variables, secret references, and VNet integration guidance
- [ ] T030 Add network security guidance in `README.md` for Azure Container Apps private SQL access
- [ ] T031 [P] Validate Docker build locally with `docker build -t secure-sql-api .`
- [ ] T032 [P] Validate local run with `uvicorn app.main:app --host 0.0.0.0 --port 8000`

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T033 [P] Add or update API documentation examples in `README.md`
- [ ] T034 [P] Add any missing error handling and logging improvements
- [ ] T035 [P] Review `app/config.py` for secure defaults and environment validation
- [ ] T036 [P] Ensure `.dockerignore` excludes secrets and unnecessary files
- [ ] T037 [P] Confirm `.specify/specs/001-sql-api/secure-sql-api.spec` and `plan.md` are aligned with implementation

---

## Dependencies & Execution Order

- Setup tasks may begin immediately.
- Foundational tasks must complete before user stories.
- User stories can proceed in parallel once foundational work is done.
- Deployment and polish tasks follow implementation completion.
