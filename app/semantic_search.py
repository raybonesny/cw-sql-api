import time
from typing import Any, Dict, List, Set, Tuple

from sqlalchemy import text

from app.config import settings
from app.database import get_engine
from app.entities.tickets import ENTITY_REGISTRY, EntityMapping, FieldMapping
from app.schemas import SemanticSearchRequest, SemanticSearchResponse


class SemanticSearchError(ValueError):
    pass


def execute_semantic_search(request: SemanticSearchRequest) -> SemanticSearchResponse:
    start_time = time.perf_counter()

    entity = ENTITY_REGISTRY.get(request.entity)
    if entity is None:
        raise SemanticSearchError(
            f"Unsupported entity '{request.entity}'. Supported entities: {', '.join(ENTITY_REGISTRY.keys())}"
        )

    selected_fields = request.select or entity.default_select
    include_names = set(request.include or [])

    select_sql, output_columns, required_includes = _build_select(entity, selected_fields)
    include_names.update(required_includes)

    where_sql, params, where_includes = _build_where(entity, request.where or [])
    include_names.update(where_includes)

    order_sql, order_includes = _build_order_by(entity, request.order_by or [])
    include_names.update(order_includes)

    joins_sql = _build_joins(entity, include_names)

    limit = request.limit or settings.query_row_limit
    if limit > settings.query_row_limit:
        limit = settings.query_row_limit

    sql = f"""
        SELECT TOP (:limit)
            {select_sql}
        FROM {entity.base_table} {entity.base_alias}
        {joins_sql}
        {where_sql}
        {order_sql}
    """

    params["limit"] = limit

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        rows = [dict(row._mapping) for row in result]

    execution_time_ms = int((time.perf_counter() - start_time) * 1000)

    return SemanticSearchResponse(
        entity=entity.name,
        columns=output_columns,
        rows=rows,
        row_count=len(rows),
        execution_time_ms=execution_time_ms,
    )


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
    field = entity.fields.get(field_name)
    if field is None:
        raise SemanticSearchError(
            f"Unsupported field '{field_name}' for entity '{entity.name}'."
        )
    return field


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


def _build_semantic_eq_clause(
    field: FieldMapping,
    value: Any,
    param_name: str,
) -> Tuple[str, Dict[str, Any]]:
    normalized_value = str(value).strip().lower()

    if field.output_name == "status_name":
        if normalized_value == "open":
            statuses = [
                "New",
                "In Progress",
                "Scheduled",
                "Waiting Customer",
                "Waiting on Customer",
                "Waiting Vendor",
                "Waiting on Vendor",
                "Escalated",
                "Reopened",
            ]
            return _build_condition_clause(field, "in", statuses, param_name)

        if normalized_value == "closed":
            statuses = [
                "Closed",
                "Completed",
                "Cancelled",
                "Canceled",
                "Resolved",
            ]
            return _build_condition_clause(field, "in", statuses, param_name)

    return _build_condition_clause(field, "eq", value, param_name)