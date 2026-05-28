# Feature Specification: Secure ConnectWise Manage SQL API Service

**Feature Branch**: `[001-secure-sql-api]`

**Created**: 2026-05-21

**Status**: Draft

**Input**: User description: "Build a secure API service that allows a Copilot agent to query a ConnectWise Manage SQL database."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Structured read-only SQL access for Copilot (Priority: P1)

As a Copilot agent, I need to submit structured query requests instead of raw SQL so that the API service can validate, sanitize, and execute only safe SELECT operations.

**Why this priority**: Structured read-only query support is the primary API requirement and is critical for preventing SQL injection and abuse.

**Independent Test**: Send a valid POST request to `/api/query` with permitted table, columns, filters, and limit; verify the response returns structured JSON rows and status `200 OK`.

**Acceptance Scenarios**:

1. **Given** a valid authenticated request, **When** the agent calls `/api/query`, **Then** the service returns `200 OK` with `rows`, `columns`, `row_count`, and `execution_time_ms`.
2. **Given** a request containing disallowed table or column names, **When** the API validates the payload, **Then** it returns `400 Bad Request` or `403 Forbidden`.

---

### User Story 2 - Enforce authentication before execution (Priority: P1)

As a secure API consumer, I need the service to authenticate every request so only authorized clients can execute queries against the SQL database.

**Why this priority**: Authentication is required to protect the SQL backend and maintain secure network access.

**Independent Test**: Issue a request without a valid bearer token and confirm the response is `401 Unauthorized`.

**Acceptance Scenarios**:

1. **Given** a missing or invalid bearer token, **When** the request is received, **Then** the service returns `401 Unauthorized`.

---

### User Story 3 - Audit log queries and results (Priority: P2)

As an auditor, I need the API to log every query request and response metadata so I can review access, query activity, and performance.

**Why this priority**: Auditing protects the environment and helps trace access to sensitive SQL data.

**Independent Test**: Examine service logs after a query request and verify entries include request metadata, subject, row count, and execution timing.

**Acceptance Scenarios**:

1. **Given** an executed query, **When** the query completes, **Then** the service logs the request subject, table, row count, and execution duration.

---

### User Story 4 - Enforce request limits and execution time bounds (Priority: P2)

As an API operator, I need row count and execution time limits so the service stays responsive and prevents excessive database usage.

**Why this priority**: Limits reduce risk from expensive or runaway queries.

**Independent Test**: Send a request with a limit above the configured maximum and verify the service rejects it with `400 Bad Request` or `429 Too Many Requests`.

**Acceptance Scenarios**:

1. **Given** a query limit greater than allowed, **When** the request is processed, **Then** the API rejects the request and returns an appropriate error.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The API MUST validate structured query payloads and reject raw SQL.
- **FR-002**: The API MUST accept only SELECT-style requests by default.
- **FR-003**: The API MUST authenticate requests before executing any query.
- **FR-004**: The API MUST sanitize identifiers and values before building SQL.
- **FR-005**: The API MUST enforce row count and execution time limits.
- **FR-006**: The API MUST log query requests, execution metadata, and outcomes for auditing.
- **FR-007**: The API MUST return results in structured JSON with row metadata.
- **FR-008**: The API MUST implement a domain-based query abstraction (e.g., tickets, configurations) rather than exposing raw database table names directly.


### Key Entities

- **QueryRequest**: Structured request body containing table, columns, filters, order by, and limit.
- **QueryResponse**: Structured JSON result containing rows, columns, row_count, execution_time_ms, and limit.
- **Authentication Token**: Bearer token used to validate calling clients.
- **Allowed Table Mapping**: A whitelist of permitted tables and columns for read-only queries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Authenticated requests to `/api/query` return `200 OK` and valid JSON response.
- **SC-002**: Unauthorized requests return `401 Unauthorized`.
- **SC-003**: Disallowed tables or columns return `400 Bad Request` or `403 Forbidden`.
- **SC-004**: Query execution is capped by row limit and time limit settings.
- **SC-005**: Audit logs capture request metadata and execution metrics.

## Assumptions

- The service uses Azure Container Apps for deployment and connects securely to SQL Server via VNet/private endpoint.
- The SQL backend supports standard SELECT syntax and ODBC connectivity.
- Allowed table and column definitions can be configured through `ALLOWED_TABLES_JSON`.
- The Copilot agent will call the service with bearer token authentication.
