import time
from typing import Any, Dict, List, Set, Tuple

from pydantic import BaseModel
from sqlalchemy import text

from app.config import settings
from app.database import get_engine
from app.entities.tickets import ENTITY_REGISTRY, EntityMapping, FieldMapping
from app.schemas import (
    SemanticCountResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
)


class SemanticSearchError(ValueError):
    pass


class SemanticSqlPreview(BaseModel):
    entity: str
    sql: str
    params: Dict[str, Any]
    columns: List[str]


FIELD_ALIASES = {
    "status": "status.name",
    "company": "company.name",
    "board": "board.name",
    "owner": "owner.name",
    "contact": "contact.name",
    "type": "type.name",
    "subtype": "subtype.name",
    "item": "item.name",
    "urgency": "urgency.name",
    "impact": "impact.name",
    "severity": "severity.name",
    "source": "source.name",
    "team": "team.name",
}


def execute_semantic_search(request: SemanticSearchRequest) -> SemanticSearchResponse:
    start_time = time.perf_counter()

    preview = build_semantic_sql_preview(request)

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(preview.sql), preview.params)
        rows = [dict(row._mapping) for row in result]

    execution_time_ms = int((time.perf_counter() - start_time) * 1000)

    return SemanticSearchResponse(
        entity=preview.entity,
        columns=preview.columns,
        rows=rows,
        row_count=len(rows),
        execution_time_ms=execution_time_ms,
    )


def execute_semantic_count(request: SemanticSearchRequest) -> SemanticCountResponse:
    start_time = time.perf_counter()

    preview = build_semantic_count_sql_preview(request)

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(preview.sql), preview.params)
        count = int(result.scalar_one())

    execution_time_ms = int((time.perf_counter() - start_time) * 1000)

    return SemanticCountResponse(
        entity=preview.entity,
        count=count,
        execution_time_ms=execution_time_ms,
    )


def build_semantic_sql_preview(request: SemanticSearchRequest) -> SemanticSqlPreview:
    entity = _get_entity(request.entity)

    selected_fields = request.select or entity.default_select
    include_names = set(request.include or [])

    select_sql, output_columns, required_includes = _build_select(entity, selected_fields)
    include_names.update(required_includes)

    where_sql, params, where_includes = _build_where(entity, request.where or [])
    include_names.update(where_includes)

    order_sql, order_includes = _build_order_by(entity, request.order_by or [])
    include_names.update(order_includes)

    joins_sql = _build_joins(entity, include_names)

    limit = request.limit or settings.QUERY_ROW_LIMIT
    if limit > settings.QUERY_ROW_LIMIT:
        limit = settings.QUERY_ROW_LIMIT

    sql = f"""
        SELECT TOP (:limit)
            {select_sql}
        FROM {entity.base_table} {entity.base_alias}
        {joins_sql}
        {where_sql}
        {order_sql}
    """

    params["limit"] = limit

    return SemanticSqlPreview(
        entity=entity.name,
        sql=_normalize_sql_whitespace(sql),
        params=params,
        columns=output_columns,
    )


def build_semantic_count_sql_preview(request: SemanticSearchRequest) -> SemanticSqlPreview:
    entity = _get_entity(request.entity)
    include_names = set(request.include or [])

    where_sql, params, where_includes = _build_where(entity, request.where or [])
    include_names.update(where_includes)

    joins_sql = _build_joins(entity, include_names)

    sql = f"""
        SELECT
            COUNT_BIG(1) AS record_count
        FROM {entity.base_table} {entity.base_alias}
        {joins_sql}
        {where_sql}
    """

    return SemanticSqlPreview(
        entity=entity.name,
        sql=_normalize_sql_whitespace(sql),
        params=params,
        columns=["record_count"],
    )


def _get_entity(entity_name: str) -> EntityMapping:
    entity = ENTITY_REGISTRY.get(entity_name)
    if entity is None:
        raise SemanticSearchError(
            f"Unsupported entity '{entity_name}'. Supported entities: {', '.join(ENTITY_REGISTRY.keys())}"
        )

    return entity


def _normalize_sql_whitespace(sql: str) -> str:
    return "\n".join(line.rstrip() for line in sql.strip().splitlines() if line.strip())


def _build_select(
    entity: EntityMapping,
    selected_fields: List[str],
) -> Tuple[str, List[str], Set[str]]:
    sql_parts: List[str] = []
    output_columns: List[str] = []
    required_includes: Set[str] = set()

    for field_name in selected_fields:
        field = _get_field(entity, field_name)
        sql_parts.append(f"{field.sql_expression} AS {field.output_name}")
        output_columns.append(field.output_name)

        if field.required_include:
            required_includes.add(field.required_include)

    return ",\n            ".join(sql_parts), output_columns, required_includes


def _build_where(
    entity: EntityMapping,
    filters: List[Any],
) -> Tuple[str, Dict[str, Any], Set[str]]:
    if not filters:
        return "", {}, set()

    clauses: List[str] = []
    params: Dict[str, Any] = {}
    required_includes: Set[str] = set()

    for index, condition in enumerate(filters):
        field = _get_field(entity, condition.field)
        param_name = f"p{index}"

        if field.required_include:
            required_includes.add(field.required_include)

        clause, clause_params = _build_condition_clause(
            field=field,
            operator=condition.operator,
            value=condition.value,
            param_name=param_name,
        )

        clauses.append(clause)
        params.update(clause_params)

    return "WHERE " + " AND ".join(clauses), params, required_includes


def _build_order_by(
    entity: EntityMapping,
    order_by: List[Any],
) -> Tuple[str, Set[str]]:
    if not order_by:
        return "", set()

    parts: List[str] = []
    required_includes: Set[str] = set()

    for item in order_by:
        field = _get_field(entity, item.field)
        direction = "DESC" if item.direction.lower() == "desc" else "ASC"
        parts.append(f"{field.sql_expression} {direction}")

        if field.required_include:
            required_includes.add(field.required_include)

    return "ORDER BY " + ", ".join(parts), required_includes


def _build_joins(entity: EntityMapping, include_names: Set[str]) -> str:
    joins: List[str] = []

    for include_name in sorted(include_names):
        include = entity.includes.get(include_name)
        if include is None:
            raise SemanticSearchError(
                f"Unsupported include '{include_name}' for entity '{entity.name}'."
            )
        joins.append(include.join_sql)

    return "\n        ".join(joins)


def _get_field(entity: EntityMapping, field_name: str) -> FieldMapping:
    normalized_field_name = _normalize_field_name(field_name)

    field = entity.fields.get(normalized_field_name)
    if field is None:
        raise SemanticSearchError(
            f"Unsupported field '{field_name}' for entity '{entity.name}'."
        )

    return field


def _normalize_field_name(field_name: str) -> str:
    normalized = field_name.strip()
    return FIELD_ALIASES.get(normalized, normalized)


def _build_condition_clause(
    field: FieldMapping,
    operator: str,
    value: Any,
    param_name: str,
) -> Tuple[str, Dict[str, Any]]:
    expression = field.sql_expression

    if operator == "eq":
        return f"{expression} = :{param_name}", {param_name: value}

    if operator == "ne":
        return f"{expression} <> :{param_name}", {param_name: value}

    if operator == "lt":
        return f"{expression} < :{param_name}", {param_name: value}

    if operator == "lte":
        return f"{expression} <= :{param_name}", {param_name: value}

    if operator == "gt":
        return f"{expression} > :{param_name}", {param_name: value}

    if operator == "gte":
        return f"{expression} >= :{param_name}", {param_name: value}

    if operator == "contains":
        return f"{expression} LIKE :{param_name}", {param_name: f"%{value}%"}

    if operator == "contains_all":
        return _build_multi_contains_clause(
            expression=expression,
            value=value,
            param_name=param_name,
            joiner="AND",
        )

    if operator == "contains_any":
        return _build_multi_contains_clause(
            expression=expression,
            value=value,
            param_name=param_name,
            joiner="OR",
        )

    if operator == "startswith":
        return f"{expression} LIKE :{param_name}", {param_name: f"{value}%"}

    if operator == "endswith":
        return f"{expression} LIKE :{param_name}", {param_name: f"%{value}"}

    if operator == "in":
        if not isinstance(value, list) or not value:
            raise SemanticSearchError("Operator 'in' requires a non-empty list value.")

        params = {}
        placeholders = []

        for item_index, item in enumerate(value):
            item_param_name = f"{param_name}_{item_index}"
            placeholders.append(f":{item_param_name}")
            params[item_param_name] = item

        return f"{expression} IN ({', '.join(placeholders)})", params

    if operator == "semantic_eq":
        return _build_semantic_eq_clause(field, value, param_name)

    raise SemanticSearchError(f"Unsupported operator '{operator}'.")


def _build_multi_contains_clause(
    expression: str,
    value: Any,
    param_name: str,
    joiner: str,
) -> Tuple[str, Dict[str, Any]]:
    if isinstance(value, str):
        terms = [term for term in value.split() if term]
    elif isinstance(value, list):
        terms = [str(term).strip() for term in value if str(term).strip()]
    else:
        raise SemanticSearchError(
            "Operators 'contains_all' and 'contains_any' require a string or non-empty list value."
        )

    if not terms:
        raise SemanticSearchError(
            "Operators 'contains_all' and 'contains_any' require at least one search term."
        )

    clauses: List[str] = []
    params: Dict[str, Any] = {}

    for index, term in enumerate(terms):
        term_param_name = f"{param_name}_{index}"
        clauses.append(f"{expression} LIKE :{term_param_name}")
        params[term_param_name] = f"%{term}%"

    return "(" + f" {joiner} ".join(clauses) + ")", params


def _build_semantic_eq_clause(
    field: FieldMapping,
    value: Any,
    param_name: str,
) -> Tuple[str, Dict[str, Any]]:
    normalized_value = str(value).strip().lower()

    if field.output_name == "status_name":
        if normalized_value == "open":
            return _build_status_open_clause()

        if normalized_value in {"closed", "completed", "complete", "done"}:
            return _build_status_closed_or_completed_clause(param_name)

        if normalized_value in {"cancelled", "canceled"}:
            return _build_status_name_contains_any_clause(
                param_name=param_name,
                terms=["cancelled", "canceled"],
            )

        if normalized_value in {
            "waiting_client",
            "waiting_on_client",
            "waiting customer",
            "waiting on customer",
            "waiting on client",
        }:
            return _build_status_name_contains_any_clause(
                param_name=param_name,
                terms=[
                    "waiting client",
                    "waiting on client",
                    "waiting customer",
                    "waiting on customer",
                    "waiting client response",
                ],
            )

        if normalized_value in {
            "waiting_vendor",
            "waiting_on_vendor",
            "waiting vendor",
            "waiting on vendor",
        }:
            return _build_status_name_contains_any_clause(
                param_name=param_name,
                terms=["waiting vendor", "waiting on vendor"],
            )

        if normalized_value in {
            "waiting_third_party",
            "waiting_3rd_party",
            "waiting on 3rd party",
            "waiting 3rd party",
            "waiting third party",
        }:
            return _build_status_name_contains_any_clause(
                param_name=param_name,
                terms=[
                    "waiting on 3rd party",
                    "waiting 3rd party",
                    "waiting on third party",
                    "waiting third party",
                ],
            )

        if normalized_value in {"scheduled", "schedule"}:
            return _build_status_name_contains_any_clause(
                param_name=param_name,
                terms=["scheduled"],
            )

        if normalized_value in {
            "scheduling_required",
            "needs_scheduling",
            "scheduling required",
        }:
            return _build_status_name_contains_any_clause(
                param_name=param_name,
                terms=["scheduling required"],
            )

        if normalized_value == "inactive":
            return "status.Inactive_Flag = 1", {}

        if normalized_value == "active":
            return "ISNULL(status.Inactive_Flag, 0) = 0", {}

    return _build_condition_clause(field, "eq", value, param_name)


def _build_status_open_clause() -> Tuple[str, Dict[str, Any]]:
    return (
        "("
        "ISNULL(status.Closed_Flag, 0) = 0 "
        "AND ISNULL(status.Inactive_Flag, 0) = 0 "
        "AND LOWER(status.Description) NOT LIKE '%complete%'"
        ")",
        {},
    )


def _build_status_closed_or_completed_clause(
    param_name: str,
) -> Tuple[str, Dict[str, Any]]:
    completed_param = f"{param_name}_completed"

    return (
        "("
        "ISNULL(status.Closed_Flag, 0) = 1 "
        f"OR LOWER(status.Description) LIKE :{completed_param}"
        ")",
        {
            completed_param: "%complete%",
        },
    )


def _build_status_name_contains_any_clause(
    param_name: str,
    terms: List[str],
) -> Tuple[str, Dict[str, Any]]:
    clauses: List[str] = []
    params: Dict[str, Any] = {}

    for index, term in enumerate(terms):
        term_param_name = f"{param_name}_{index}"
        clauses.append(f"LOWER(status.Description) LIKE :{term_param_name}")
        params[term_param_name] = f"%{term.lower()}%"

    return "(" + " OR ".join(clauses) + ")", params