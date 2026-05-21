from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FilterCondition(BaseModel):
    field: str
    operator: str
    value: Any


class OrderBy(BaseModel):
    field: str
    direction: str = Field("asc", pattern="^(asc|desc)$")


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
