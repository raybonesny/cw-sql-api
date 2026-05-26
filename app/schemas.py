from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel


class FilterCondition(BaseModel):
    field: str
    operator: Literal[
        "eq",
        "ne",
        "lt",
        "lte",
        "gt",
        "gte",
        "in",
        "contains",
        "startswith",
        "endswith",
    ]
    value: Any


class OrderBy(BaseModel):
    field: str
    direction: Literal["asc", "desc"] = "asc"


class QueryRequest(BaseModel):
    table: str
    columns: Optional[List[str]] = None
    filters: Optional[List[FilterCondition]] = None
    order_by: Optional[List[OrderBy]] = None
    limit: Optional[int] = None


class QueryResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int