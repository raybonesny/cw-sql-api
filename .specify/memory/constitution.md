# CW SQL API Constitution

## Core Principles

### I. Read-Only First (NON-NEGOTIABLE)
All database interactions must be read-only by default. Only SELECT statements are permitted unless explicitly approved. No INSERT, UPDATE, DELETE, or schema-altering commands are allowed.

### II. Query Validation Required
All queries must be programmatically validated before execution. Queries must conform to allowed patterns and reject any unsafe constructs including dynamic SQL, nested execution, or system-level access.

### III. No Raw SQL Input
The system must never execute raw user-provided SQL. All requests must follow a structured query format that is parsed and validated before being translated into executable SQL.

### IV. Parameterization Enforcement
All database queries must use parameterized inputs. String concatenation or direct variable substitution into SQL statements is strictly prohibited.

### V. Security & Injection Protection
The system must actively detect and block SQL injection attempts. Inputs must be sanitized and validated against known attack patterns.

### VI. Observability & Audit Logging
All queries, execution metadata, and responses must be logged. Logs must include:
- Query structure (sanitized)
- Execution time
- Result metadata
- Request origin (if available)

### VII. Data Protection & Masking
Sensitive data (such as personal, financial, or credential information) must be masked, restricted, or excluded from responses. Access must follow least-privilege principles.

---

## Security Requirements

- API must enforce authentication before executing any query
- SQL connections must be private (VNET / secure access only)
- Queries must enforce row limits and execution timeouts
- Errors must not expose SQL schema or internal database details
- Logs must not expose sensitive data

---

## Performance & Constraints

- Queries must include result limits (TOP / LIMIT enforcement)
- Long-running queries must be blocked or timed out
- API must fail fast on validation errors
- Prevent full-table scans unless explicitly approved

---

## Development Workflow

- All features must comply with constitution before implementation
- Validation logic must be implemented before query execution logic
- Changes to query structure must be reviewed against security rules
- Logging and auditing must be included in all query endpoints

---

## Governance

This constitution is the authoritative source of truth for all system behavior.

- All implementations must comply with these principles


---

**Version**: 1.0.0  
**Ratified**: 2026-05-19  
**Last Amended**: 2026-05-19
