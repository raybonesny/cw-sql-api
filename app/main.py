import json
import logging
from typing import Any, List

from fastapi import Depends, FastAPI, HTTPException, Request, status

from app.auth import verify_token
from app.config import validate_environment
from app.copilot_tickets import build_semantic_count_request_from_copilot
from app.database import build_select_query, execute_select
from app.entities.tickets import ENTITY_REGISTRY
from app.schemas import (
    CopilotSemanticCountJsonRequest,
    CopilotSemanticSearchJsonRequest,
    CopilotSlaSearchJsonRequest,
    CopilotTicketCountRequest,
    CopilotTicketNotesJsonRequest,
    FilterCondition,
    QueryRequest,
    QueryResponse,
    SemanticCountResponse,
    SemanticFilterCondition,
    SemanticOrderBy,
    SemanticSearchRequest,
    SemanticSearchResponse,
    TicketNotesRequest,
    TicketNotesResponse,
)
from app.semantic_maps import SEMANTIC_STATUS_FIELDS, resolve_status_filter
from app.semantic_search import (
    SemanticSearchError,
    build_semantic_count_sql_preview,
    build_semantic_sql_preview,
    execute_semantic_count,
    execute_semantic_search,
)
from app.ticket_notes import (
    build_ticket_notes_sql_preview,
    execute_ticket_notes_search,
)

app = FastAPI(title="CW Secure SQL API", version="0.2.0")

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


def get_client_ip(http_request: Request) -> str | None:
    try:
        return http_request.client.host if http_request.client else None
    except Exception:
        return None


def clean_json_text(json_text: str) -> str:
    cleaned = json_text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()

        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    return cleaned


def parse_json_text(json_text: str, label: str) -> Any:
    cleaned = clean_json_text(json_text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise SemanticSearchError(f"Invalid {label}. Expected valid JSON. {e}")


def parse_copilot_filters_json(filters_json: str) -> list[SemanticFilterCondition]:
    """
    Parses Copilot-provided JSON text into SemanticFilterCondition objects.

    Accepts either:
    [
      {"field": "company", "operator": "contains", "value": "Oaklawn"}
    ]

    or:
    {
      "where": [
        {"field": "company", "operator": "contains", "value": "Oaklawn"}
      ]
    }
    """

    parsed = parse_json_text(filters_json, "filters_json")

    if isinstance(parsed, dict):
        parsed_filters = parsed.get("where") or parsed.get("filters")
    else:
        parsed_filters = parsed

    if not isinstance(parsed_filters, list) or not parsed_filters:
        raise SemanticSearchError(
            "filters_json must be a non-empty JSON array of filter objects."
        )

    filters: list[SemanticFilterCondition] = []

    for item in parsed_filters:
        if not isinstance(item, dict):
            raise SemanticSearchError(
                "Each filters_json item must be an object with field, operator, and value."
            )

        filters.append(SemanticFilterCondition(**item))

    return filters


def parse_optional_copilot_filters_json(
    filters_json: str | None,
) -> list[SemanticFilterCondition] | None:
    if filters_json is None or not filters_json.strip():
        return None

    return parse_copilot_filters_json(filters_json)


def parse_copilot_select_json(select_json: str | None) -> list[str] | None:
    """
    Parses selected fields from Copilot-provided JSON text.

    Accepts either:
    ["id", "company", "summary", "status"]

    or:
    {
      "select": ["id", "company", "summary", "status"]
    }
    """

    if select_json is None or not select_json.strip():
        return None

    parsed = parse_json_text(select_json, "select_json")

    if isinstance(parsed, dict):
        parsed_select = parsed.get("select") or parsed.get("fields") or parsed.get("columns")
    else:
        parsed_select = parsed

    if not isinstance(parsed_select, list) or not parsed_select:
        raise SemanticSearchError(
            "select_json must be a non-empty JSON array of field names."
        )

    return [str(item).strip() for item in parsed_select if str(item).strip()]


def parse_copilot_order_by_json(
    order_by_json: str | None,
) -> list[SemanticOrderBy] | None:
    """
    Parses sort instructions from Copilot-provided JSON text.

    Accepts either:
    [{"field": "last_updated", "direction": "desc"}]

    or:
    {
      "order_by": [{"field": "last_updated", "direction": "desc"}]
    }
    """

    if order_by_json is None or not order_by_json.strip():
        return None

    parsed = parse_json_text(order_by_json, "order_by_json")

    if isinstance(parsed, dict):
        parsed_order_by = parsed.get("order_by") or parsed.get("sort")
    else:
        parsed_order_by = parsed

    if not isinstance(parsed_order_by, list) or not parsed_order_by:
        raise SemanticSearchError(
            "order_by_json must be a non-empty JSON array of sort objects."
        )

    order_by: list[SemanticOrderBy] = []

    for item in parsed_order_by:
        if not isinstance(item, dict):
            raise SemanticSearchError(
                "Each order_by_json item must be an object with field and optional direction."
            )

        order_by.append(SemanticOrderBy(**item))

    return order_by


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/search/entities")
def list_search_entities(_: Any = Depends(verify_token)) -> dict[str, Any]:
    return {
        "entities": sorted(ENTITY_REGISTRY.keys()),
    }


@app.get("/api/search/entities/{entity_name}")
def get_search_entity(
    entity_name: str,
    _: Any = Depends(verify_token),
) -> dict[str, Any]:
    entity = ENTITY_REGISTRY.get(entity_name)

    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unsupported entity '{entity_name}'.",
        )

    return {
        "entity": entity.name,
        "base_table": entity.base_table,
        "default_select": entity.default_select,
        "fields": sorted(entity.fields.keys()),
        "includes": sorted(entity.includes.keys()),
    }


@app.post("/api/query", response_model=QueryResponse)
def query_api(
    request_body: QueryRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> QueryResponse:

    client_ip = get_client_ip(http_request)

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


@app.post("/api/search/preview")
def semantic_search_preview_api(
    request_body: SemanticSearchRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> dict[str, Any]:

    client_ip = get_client_ip(http_request)

    try:
        preview = build_semantic_sql_preview(request_body)

        logger.info(
            "semantic_search_preview_generated client_ip=%s entity=%s",
            client_ip,
            request_body.entity,
        )

        return preview.model_dump()

    except SemanticSearchError as se:
        logger.warning(
            "semantic_search_preview_rejected client_ip=%s entity=%s reason=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except Exception as e:
        logger.error(
            "semantic_search_preview_unexpected_error client_ip=%s entity=%s error=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/copilot/tickets/count", response_model=SemanticCountResponse)
def copilot_ticket_count_api(
    request_body: CopilotTicketCountRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> SemanticCountResponse:

    client_ip = get_client_ip(http_request)

    try:
        semantic_request = build_semantic_count_request_from_copilot(request_body)
        response = execute_semantic_count(semantic_request)

        logger.info(
            "copilot_ticket_count_executed client_ip=%s count=%s execution_time_ms=%s filters=%s",
            client_ip,
            response.count,
            response.execution_time_ms,
            request_body.model_dump(exclude_none=True),
        )

        return response

    except SemanticSearchError as se:
        logger.warning(
            "copilot_ticket_count_rejected client_ip=%s reason=%s",
            client_ip,
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except RuntimeError as re:
        logger.error(
            "copilot_ticket_count_failed client_ip=%s error=%s",
            client_ip,
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        logger.error(
            "copilot_ticket_count_unexpected_error client_ip=%s error=%s",
            client_ip,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/copilot/tickets/count/json", response_model=SemanticCountResponse)
def copilot_ticket_count_json_api(
    request_body: CopilotSemanticCountJsonRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> SemanticCountResponse:

    client_ip = get_client_ip(http_request)

    try:
        filters = parse_copilot_filters_json(request_body.filters_json)

        semantic_request = SemanticSearchRequest(
            entity=request_body.entity,
            where=filters,
        )

        response = execute_semantic_count(semantic_request)

        logger.info(
            "copilot_ticket_count_json_executed client_ip=%s entity=%s count=%s execution_time_ms=%s filters=%s",
            client_ip,
            semantic_request.entity,
            response.count,
            response.execution_time_ms,
            [item.model_dump() for item in filters],
        )

        return response

    except SemanticSearchError as se:
        logger.warning(
            "copilot_ticket_count_json_rejected client_ip=%s reason=%s",
            client_ip,
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except RuntimeError as re:
        logger.error(
            "copilot_ticket_count_json_failed client_ip=%s error=%s",
            client_ip,
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        logger.error(
            "copilot_ticket_count_json_unexpected_error client_ip=%s error=%s",
            client_ip,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/copilot/tickets/search/json", response_model=SemanticSearchResponse)
def copilot_ticket_search_json_api(
    request_body: CopilotSemanticSearchJsonRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> SemanticSearchResponse:

    client_ip = get_client_ip(http_request)

    try:
        filters = parse_optional_copilot_filters_json(request_body.filters_json)
        select = parse_copilot_select_json(request_body.select_json)
        order_by = parse_copilot_order_by_json(request_body.order_by_json)

        semantic_request = SemanticSearchRequest(
            entity=request_body.entity,
            select=select,
            where=filters,
            order_by=order_by,
            limit=request_body.limit,
        )

        response = execute_semantic_search(semantic_request)

        logger.info(
            "copilot_ticket_search_json_executed client_ip=%s entity=%s row_count=%s execution_time_ms=%s filters=%s select=%s order_by=%s limit=%s",
            client_ip,
            semantic_request.entity,
            response.row_count,
            response.execution_time_ms,
            [item.model_dump() for item in filters] if filters else None,
            select,
            [item.model_dump() for item in order_by] if order_by else None,
            request_body.limit,
        )

        return response

    except SemanticSearchError as se:
        logger.warning(
            "copilot_ticket_search_json_rejected client_ip=%s reason=%s",
            client_ip,
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except RuntimeError as re:
        logger.error(
            "copilot_ticket_search_json_failed client_ip=%s error=%s",
            client_ip,
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        logger.error(
            "copilot_ticket_search_json_unexpected_error client_ip=%s error=%s",
            client_ip,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/copilot/tickets/sla/search/json", response_model=SemanticSearchResponse)
def copilot_ticket_sla_search_json_api(
    request_body: CopilotSlaSearchJsonRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> SemanticSearchResponse:

    client_ip = get_client_ip(http_request)

    try:
        filters = parse_optional_copilot_filters_json(request_body.filters_json)
        select = parse_copilot_select_json(request_body.select_json)
        order_by = parse_copilot_order_by_json(request_body.order_by_json)

        semantic_request = SemanticSearchRequest(
            entity=request_body.entity,
            select=select,
            where=filters,
            order_by=order_by,
            limit=request_body.limit,
        )

        response = execute_semantic_search(semantic_request)

        logger.info(
            "copilot_ticket_sla_search_json_executed client_ip=%s entity=%s row_count=%s execution_time_ms=%s filters=%s select=%s order_by=%s limit=%s",
            client_ip,
            semantic_request.entity,
            response.row_count,
            response.execution_time_ms,
            [item.model_dump() for item in filters] if filters else None,
            select,
            [item.model_dump() for item in order_by] if order_by else None,
            request_body.limit,
        )

        return response

    except SemanticSearchError as se:
        logger.warning(
            "copilot_ticket_sla_search_json_rejected client_ip=%s reason=%s",
            client_ip,
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except RuntimeError as re:
        logger.error(
            "copilot_ticket_sla_search_json_failed client_ip=%s error=%s",
            client_ip,
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        logger.error(
            "copilot_ticket_sla_search_json_unexpected_error client_ip=%s error=%s",
            client_ip,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/copilot/tickets/notes/json", response_model=TicketNotesResponse)
def copilot_ticket_notes_json_api(
    request_body: CopilotTicketNotesJsonRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> TicketNotesResponse:

    client_ip = get_client_ip(http_request)

    try:
        filters = parse_copilot_filters_json(request_body.filters_json)

        notes_request = TicketNotesRequest(
            ticket_where=filters,
            limit_tickets=request_body.limit_tickets,
            limit_notes=request_body.limit_notes,
            include_internal=request_body.include_internal,
        )

        response = execute_ticket_notes_search(notes_request)

        logger.info(
            "copilot_ticket_notes_json_executed client_ip=%s row_count=%s execution_time_ms=%s filters=%s limit_tickets=%s limit_notes=%s include_internal=%s",
            client_ip,
            response.row_count,
            response.execution_time_ms,
            [item.model_dump() for item in filters],
            request_body.limit_tickets,
            request_body.limit_notes,
            request_body.include_internal,
        )

        return response

    except SemanticSearchError as se:
        logger.warning(
            "copilot_ticket_notes_json_rejected client_ip=%s reason=%s",
            client_ip,
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except RuntimeError as re:
        logger.error(
            "copilot_ticket_notes_json_failed client_ip=%s error=%s",
            client_ip,
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        logger.error(
            "copilot_ticket_notes_json_unexpected_error client_ip=%s error=%s",
            client_ip,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.get("/api/copilot/tickets/count", response_model=SemanticCountResponse)
def copilot_ticket_count_get_api(
    http_request: Request,
    company_contains: str | None = None,
    summary_contains: str | None = None,
    summary_contains_all: str | None = None,
    status_filter: str | None = None,
    board_contains: str | None = None,
    owner_contains: str | None = None,
    date_entered_gte: str | None = None,
    date_entered_lte: str | None = None,
    last_updated_gte: str | None = None,
    last_updated_lte: str | None = None,
    _: Any = Depends(verify_token),
) -> SemanticCountResponse:

    client_ip = get_client_ip(http_request)

    try:
        summary_terms = None
        if summary_contains_all:
            summary_terms = [
                term.strip()
                for term in summary_contains_all.split(",")
                if term.strip()
            ]

        request_body = CopilotTicketCountRequest(
            company_contains=company_contains,
            summary_contains=summary_contains,
            summary_contains_all=summary_terms,
            status=status_filter,
            board_contains=board_contains,
            owner_contains=owner_contains,
            date_entered_gte=date_entered_gte,
            date_entered_lte=date_entered_lte,
            last_updated_gte=last_updated_gte,
            last_updated_lte=last_updated_lte,
        )

        semantic_request = build_semantic_count_request_from_copilot(request_body)
        response = execute_semantic_count(semantic_request)

        logger.info(
            "copilot_ticket_count_get_executed client_ip=%s count=%s execution_time_ms=%s filters=%s",
            client_ip,
            response.count,
            response.execution_time_ms,
            request_body.model_dump(exclude_none=True),
        )

        return response

    except SemanticSearchError as se:
        logger.warning(
            "copilot_ticket_count_get_rejected client_ip=%s reason=%s",
            client_ip,
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except RuntimeError as re:
        logger.error(
            "copilot_ticket_count_get_failed client_ip=%s error=%s",
            client_ip,
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        logger.error(
            "copilot_ticket_count_get_unexpected_error client_ip=%s error=%s",
            client_ip,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/search/count/preview")
def semantic_count_preview_api(
    request_body: SemanticSearchRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> dict[str, Any]:

    client_ip = get_client_ip(http_request)

    try:
        preview = build_semantic_count_sql_preview(request_body)

        logger.info(
            "semantic_count_preview_generated client_ip=%s entity=%s",
            client_ip,
            request_body.entity,
        )

        return preview.model_dump()

    except SemanticSearchError as se:
        logger.warning(
            "semantic_count_preview_rejected client_ip=%s entity=%s reason=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except Exception as e:
        logger.error(
            "semantic_count_preview_unexpected_error client_ip=%s entity=%s error=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/search/count", response_model=SemanticCountResponse)
def semantic_count_api(
    request_body: SemanticSearchRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> SemanticCountResponse:

    client_ip = get_client_ip(http_request)

    try:
        response = execute_semantic_count(request_body)

        logger.info(
            "semantic_count_executed client_ip=%s entity=%s count=%s execution_time_ms=%s",
            client_ip,
            request_body.entity,
            response.count,
            response.execution_time_ms,
        )

        return response

    except SemanticSearchError as se:
        logger.warning(
            "semantic_count_rejected client_ip=%s entity=%s reason=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except RuntimeError as re:
        logger.error(
            "semantic_count_failed client_ip=%s entity=%s error=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        logger.error(
            "semantic_count_unexpected_error client_ip=%s entity=%s error=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/search/ticket-notes/preview")
def ticket_notes_preview_api(
    request_body: TicketNotesRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> dict[str, Any]:

    client_ip = get_client_ip(http_request)

    try:
        preview = build_ticket_notes_sql_preview(request_body)

        logger.info(
            "ticket_notes_preview_generated client_ip=%s row_limit=%s note_limit=%s",
            client_ip,
            request_body.limit_tickets,
            request_body.limit_notes,
        )

        return preview.model_dump()

    except SemanticSearchError as se:
        logger.warning(
            "ticket_notes_preview_rejected client_ip=%s reason=%s",
            client_ip,
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except Exception as e:
        logger.error(
            "ticket_notes_preview_unexpected_error client_ip=%s error=%s",
            client_ip,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/search/ticket-notes", response_model=TicketNotesResponse)
def ticket_notes_api(
    request_body: TicketNotesRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> TicketNotesResponse:

    client_ip = get_client_ip(http_request)

    try:
        response = execute_ticket_notes_search(request_body)

        logger.info(
            "ticket_notes_executed client_ip=%s row_count=%s execution_time_ms=%s",
            client_ip,
            response.row_count,
            response.execution_time_ms,
        )

        return response

    except SemanticSearchError as se:
        logger.warning(
            "ticket_notes_rejected client_ip=%s reason=%s",
            client_ip,
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except RuntimeError as re:
        logger.error(
            "ticket_notes_failed client_ip=%s error=%s",
            client_ip,
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        logger.error(
            "ticket_notes_unexpected_error client_ip=%s error=%s",
            client_ip,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )


@app.post("/api/search", response_model=SemanticSearchResponse)
def semantic_search_api(
    request_body: SemanticSearchRequest,
    http_request: Request,
    _: Any = Depends(verify_token),
) -> SemanticSearchResponse:

    client_ip = get_client_ip(http_request)

    try:
        response = execute_semantic_search(request_body)

        logger.info(
            "semantic_search_executed client_ip=%s entity=%s row_count=%s execution_time_ms=%s",
            client_ip,
            request_body.entity,
            response.row_count,
            response.execution_time_ms,
        )

        return response

    except SemanticSearchError as se:
        logger.warning(
            "semantic_search_rejected client_ip=%s entity=%s reason=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(se),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(se),
        )

    except RuntimeError as re:
        logger.error(
            "semantic_search_failed client_ip=%s entity=%s error=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(re),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )

    except Exception as e:
        logger.error(
            "semantic_search_unexpected_error client_ip=%s entity=%s error=%s",
            client_ip,
            getattr(request_body, "entity", None),
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )