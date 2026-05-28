from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


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
    expand: Optional[List[str]] = None
    limit: Optional[int] = None


class QueryResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int


class SemanticFilterCondition(BaseModel):
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
        "semantic_eq",
    ] = "eq"
    value: Any


class SemanticOrderBy(BaseModel):
    field: str
    direction: Literal["asc", "desc"] = "asc"


class SemanticSearchRequest(BaseModel):
    entity: Literal["ticket"]
    select: Optional[List[str]] = None
    where: Optional[List[SemanticFilterCondition]] = None
    include: Optional[List[str]] = None
    order_by: Optional[List[SemanticOrderBy]] = None
    limit: Optional[int] = Field(default=None, ge=1)


class SemanticSearchResponse(BaseModel):
    entity: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int