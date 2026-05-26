import time
from typing import Any, Dict, List, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_allowed_tables, get_row_limit, settings
from app.schemas import QueryRequest


from app.relationships import ALLOWED_EXPANDS


def get_connection_string() -> str:
    """
    Build a SQLAlchemy connection string for SQL Server via pyodbc.
    NOTE: TrustServerCertificate is included to avoid TLS validation issues in some environments.
    """
    driver = settings.DB_DRIVER.replace(" ", "+")
    return (
        f"mssql+pyodbc://{settings.DB_USERNAME}:{settings.DB_PASSWORD}"
        f"@{settings.DB_SERVER}/{settings.DB_DATABASE}"
        f"?driver={driver}"
        "&TrustServerCertificate=yes"
    )


def get_engine() -> Engine:
    connection_string = get_connection_string()

    engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    return engine


def execute_select(sql: str, params: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]], int]:
    """
    Execute a parameterized SELECT statement safely and return:
      (columns, rows, execution_time_ms)

    - Uses SQLAlchemy text() + bound parameters.
    - Assumes sql is already restricted to SELECT-only by your compiler.
    """
    engine = get_engine()
    start = time.perf_counter()

    try:
        stmt = text(sql)

        with engine.connect() as conn:
            result = conn.execute(stmt, params)
            columns = list(result.keys())
            rows = [dict(r._mapping) for r in result.fetchall()]

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return columns, rows, elapsed_ms

    except SQLAlchemyError as e:
        # Do NOT leak SQL, schema, or driver details outward
        raise RuntimeError("Database query failed") from e


def build_where_clause(
    filters: List[Any],
    allowed_columns: List[str],
    params: Dict[str, Any],
    table_alias: str = "s",
) -> Tuple[str, Dict[str, Any]]:
    """
    Build a parameterized WHERE clause from structured filters.
    Supported operators: eq, ne, lt, lte, gt, gte, in, contains, startswith, endswith
    """
    clauses: List[str] = []
    param_index = len(params)  # start after existing params (e.g., limit)

    for f in filters:
        field = f.field
        op = f.operator
        value = f.value

        # Validate field against allowlist
        if field not in allowed_columns:
            raise ValueError(f"Filter field '{field}' is not allowed")

        col = f"{table_alias}.[{field}]"

        # Unique parameter base name
        pname = f"p{param_index}"
        param_index += 1

        if op == "eq":
            clauses.append(f"{col} = :{pname}")
            params[pname] = value

        elif op == "ne":
            clauses.append(f"{col} <> :{pname}")
            params[pname] = value

        elif op == "lt":
            clauses.append(f"{col} < :{pname}")
            params[pname] = value

        elif op == "lte":
            clauses.append(f"{col} <= :{pname}")
            params[pname] = value

        elif op == "gt":
            clauses.append(f"{col} > :{pname}")
            params[pname] = value

        elif op == "gte":
            clauses.append(f"{col} >= :{pname}")
            params[pname] = value

        elif op == "contains":
            if not isinstance(value, str):
                raise ValueError(f"Operator 'contains' requires a string value for field '{field}'")
            clauses.append(f"{col} LIKE :{pname}")
            params[pname] = f"%{value}%"

        elif op == "startswith":
            if not isinstance(value, str):
                raise ValueError(f"Operator 'startswith' requires a string value for field '{field}'")
            clauses.append(f"{col} LIKE :{pname}")
            params[pname] = f"{value}%"

        elif op == "endswith":
            if not isinstance(value, str):
                raise ValueError(f"Operator 'endswith' requires a string value for field '{field}'")
            clauses.append(f"{col} LIKE :{pname}")
            params[pname] = f"%{value}"

        elif op == "in":
            if not isinstance(value, list):
                raise ValueError(f"Operator 'in' requires a list value for field '{field}'")
            if len(value) == 0:
                raise ValueError(f"Operator 'in' requires a non-empty list for field '{field}'")

            in_placeholders: List[str] = []
            for i, item in enumerate(value):
                in_name = f"{pname}_{i}"
                in_placeholders.append(f":{in_name}")
                params[in_name] = item

            clauses.append(f"{col} IN ({', '.join(in_placeholders)})")

        else:
            raise ValueError(f"Unsupported operator '{op}'")

    if not clauses:
        return "", params

    return "WHERE " + " AND ".join(clauses), params


def build_expand_clauses(
    base_table: str,
    expands: List[str],
    allowed_tables: Dict[str, List[str]],
) -> Tuple[str, List[str]]:
    """
    Builds safe JOIN clauses and expanded SELECT expressions for allowed relationships.
    """
    if not expands:
        return "", []

    join_clauses: List[str] = []
    expanded_selects: List[str] = []

    for expand in expands:
        if expand not in ALLOWED_EXPANDS.get(base_table, {}):
            raise ValueError(f"Expand '{expand}' is not allowed for table '{base_table}'")

        cfg = ALLOWED_EXPANDS[base_table][expand]

        target_table = cfg["table"]
        join_alias = cfg["join_alias"]
        base_alias = cfg["base_alias"]
        left_key = cfg["left_key"]
        right_key = cfg["right_key"]
        default_columns = cfg["default_columns"]

        # Make sure expanded table is also in allowlist
        if target_table not in allowed_tables:
            raise ValueError(f"Expanded table '{target_table}' is not allowed")

        target_allowed_columns = allowed_tables[target_table]

        for col in default_columns:
            if col not in target_allowed_columns:
                raise ValueError(
                    f"Expanded column '{col}' is not allowed for table '{target_table}'"
                )

            expanded_selects.append(
                f"{join_alias}.[{col}] AS [{expand}_{col}]"
            )

        join_clauses.append(
            f"LEFT JOIN [{target_table}] {join_alias} "
            f"ON {base_alias}.[{left_key}] = {join_alias}.[{right_key}]"
        )

    return " ".join(join_clauses), expanded_selects


def build_select_query(request: QueryRequest) -> Tuple[str, Dict[str, Any]]:
    """
    Converts a QueryRequest into a safe parameterized SQL query with:
      - SELECT TOP (:limit) ...
      - optional WHERE (filters)
      - optional ORDER BY
      - optional controlled expands
    """
    allowed_tables = get_allowed_tables()

    base_table = request.table
    base_alias = "s"

    # 1. Validate table
    if base_table not in allowed_tables:
        raise ValueError(f"Table '{base_table}' is not allowed")

    allowed_columns = allowed_tables[base_table]

    # 2. Validate columns
    columns = request.columns or allowed_columns
    for col in columns:
        if col not in allowed_columns:
            raise ValueError(f"Column '{col}' is not allowed in table '{base_table}'")

    # 3. Apply LIMIT
    limit = get_row_limit(request.limit or 0)

    # 4. Expanded JOINs + expanded SELECT columns
    join_clause = ""
    expanded_selects: List[str] = []
    if request.expand:
        join_clause, expanded_selects = build_expand_clauses(
            base_table=base_table,
            expands=request.expand,
            allowed_tables=allowed_tables,
        )

    # 5. Build SELECT list
    base_selects = [f"{base_alias}.[{col}] AS [{col}]" for col in columns]
    all_selects = base_selects + expanded_selects
    column_list = ", ".join(all_selects)

    select_clause = f"SELECT TOP (:limit) {column_list} FROM [{base_table}] {base_alias}"

    # 6. Params
    params: Dict[str, Any] = {"limit": limit}

    # 7. WHERE
    where_clause = ""
    if request.filters:
        where_clause, params = build_where_clause(
            filters=request.filters,
            allowed_columns=allowed_columns,
            params=params,
            table_alias=base_alias,
        )

    # 8. ORDER BY
    order_clause = ""
    if request.order_by:
        order_parts: List[str] = []
        for order in request.order_by:
            field = order.field
            direction = (order.direction or "asc").lower()

            if field not in allowed_columns:
                raise ValueError(f"ORDER BY field '{field}' is not allowed")

            if direction not in ("asc", "desc"):
                raise ValueError(f"Invalid order direction '{direction}' for field '{field}'")

            order_parts.append(f"{base_alias}.[{field}] {direction.upper()}")

        if order_parts:
            order_clause = "ORDER BY " + ", ".join(order_parts)

    sql = f"{select_clause} {join_clause} {where_clause} {order_clause}".strip()
    return sql, params