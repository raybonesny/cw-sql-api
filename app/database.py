import time
from typing import Any, Dict, List, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_allowed_tables, get_row_limit, settings
from app.schemas import QueryRequest


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

        col = f"[{field}]"

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

            # Expand list into (:pN_0, :pN_1, ...)
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


def build_select_query(request: QueryRequest) -> Tuple[str, Dict[str, Any]]:
    """
    Converts a QueryRequest into a safe parameterized SQL query with:
      - SELECT TOP (:limit) ...
      - optional WHERE (filters)
      - optional ORDER BY
    """
    allowed_tables = get_allowed_tables()

    # 1. Validate table
    table = request.table
    if table not in allowed_tables:
        raise ValueError(f"Table '{table}' is not allowed")

    allowed_columns = allowed_tables[table]

    # 2. Validate columns
    columns = request.columns or allowed_columns
    for col in columns:
        if col not in allowed_columns:
            raise ValueError(f"Column '{col}' is not allowed in table '{table}'")

    # 3. Apply LIMIT (safe enforcement)
    limit = get_row_limit(request.limit or 0)

    # 4. Build SELECT clause safely
    column_list = ", ".join(f"[{col}]" for col in columns)
    select_clause = f"SELECT TOP (:limit) {column_list} FROM [{table}]"

    # 5. Prepare parameters
    params: Dict[str, Any] = {"limit": limit}

    # 6. WHERE clause (filters)
    where_clause = ""
    if request.filters:
        where_clause, params = build_where_clause(
            filters=request.filters,
            allowed_columns=allowed_columns,
            params=params,
        )

    # 7. ORDER BY clause (safe)
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

            order_parts.append(f"[{field}] {direction.upper()}")

        if order_parts:
            order_clause = "ORDER BY " + ", ".join(order_parts)

    sql = f"{select_clause} {where_clause} {order_clause}".strip()
    return sql, params