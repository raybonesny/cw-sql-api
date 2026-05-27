import logging
from typing import Any, List

from fastapi import Depends, FastAPI, HTTPException, Request, status

from app.auth import verify_token
from app.config import validate_environment
from app.database import build_select_query, execute_select
from app.schemas import QueryRequest, QueryResponse, FilterCondition
from app.semantic_maps import SEMANTIC_STATUS_FIELDS, resolve_status_filter

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
    try:
        validate_environment()
        logger.info("Startup validation succeeded.")
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")
        raise


def apply_semantic_filters(request_body: QueryRequest) -> QueryRequest:
    """
    Converts generic semantic filters into concrete expanded-table filters.
    """

    if not request_body.filters:
        return request_body

    new_filters: List[FilterCondition] = []
    expands = list(request_body.expand or [])

    for f in request_body.filters:
        field_lower = f.field.lower()

        if field_lower in SEMANTIC_STATUS_FIELDS:
            resolved = resolve_status_filter(str(f.value))
            new_filters.append(FilterCondition(**resolved))

            if "SR_Status" not in expands:
                expands.append("SR_Status")

            continue

        new_filters.append(f)

    request_body.filters = new_filters
    request_body.expand = expands

    return request_body


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
def query_api(
    request_body: QueryRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> QueryResponse:

    client_ip = None
    try:
        client_ip = http_request.client.host if http_request.client else None
    except Exception:
        client_ip = None

    try:
        request_body = apply_semantic_filters(request_body)

        sql, params = build_select_query(request_body)

        columns, rows, execution_time_ms = execute_select(sql, params)

        logger.info(
            "query_executed client_ip=%s table=%s row_count=%s execution_time_ms=%s expands=%s",
            client_ip,
            request_body.table,
            len(rows),
            execution_time_ms,
            request_body.expand,
        )

        return QueryResponse(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=execution_time_ms,
        )

    except ValueError as ve:
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
