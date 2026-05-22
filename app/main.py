import logging
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status

from app.auth import verify_token
from app.config import validate_environment
from app.database import build_select_query, execute_select
from app.schemas import QueryRequest, QueryResponse

app = FastAPI(title="CW Secure SQL API", version="0.1.0")

# -----------------------
# Logging Setup
# -----------------------
logger = logging.getLogger("cw_sql_api")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@app.on_event("startup")
def on_startup() -> None:
    """
    Validate required environment variables at startup.
    Fails fast if critical settings are missing.
    """
    try:
        validate_environment()
        logger.info("Startup validation succeeded.")
    except Exception as e:
        # Fail fast - container should not start if env is invalid
        logger.error(f"Startup validation failed: {e}")
        raise


# -----------------------
# Health Check
# -----------------------
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# -----------------------
# Query Endpoint
# -----------------------
@app.post("/api/query", response_model=QueryResponse)
def query_api(
    request_body: QueryRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> QueryResponse:
    """
    Accepts a structured query payload, compiles it to parameterized SQL,
    executes safely, and returns rows + metadata.

    Auth: Bearer token required.
    """
    client_ip = None
    try:
        client_ip = http_request.client.host if http_request.client else None
    except Exception:
        client_ip = None

    try:
        # Compile structured request -> SQL + params
        sql, params = build_select_query(request_body)

        # Execute safely
        columns, rows, execution_time_ms = execute_select(sql, params)

        # Audit log (DO NOT log SQL params/values)
        logger.info(
            "query_executed client_ip=%s table=%s columns_requested=%s row_count=%s execution_time_ms=%s",
            client_ip,
            request_body.table,
            len(request_body.columns) if request_body.columns else "ALL_ALLOWED",
            len(rows),
            execution_time_ms,
        )

        return QueryResponse(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=execution_time_ms,
        )

    except ValueError as ve:
        # Validation errors: allowlist violations, unsupported operators, etc.
        logger.warning(
            "query_rejected client_ip=%s table=%s reason=%s",
            client_ip,
            getattr(request_body, "table", None),
            str(ve),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )

    except RuntimeError as re:
        # Database failure (sanitized)
        logger.error(
            "query_failed client_ip=%s table=%s error=%s",
            client_ip,
            getattr(request_body, "table", None),
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        # Catch-all (sanitized)
        logger.error(
            "unexpected_error client_ip=%s table=%s error=%s",
            client_ip,
            getattr(request_body, "table", None),
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )