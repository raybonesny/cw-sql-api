from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


def normalize_token(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_")


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

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: Any) -> str:
        return normalize_token(value)


class OrderBy(BaseModel):
    field: str
    direction: Literal["asc", "desc"] = "asc"

    @field_validator("direction", mode="before")
    @classmethod
    def normalize_direction(cls, value: Any) -> str:
        return normalize_token(value)


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
        "contains_all",
        "contains_any",
        "startswith",
        "endswith",
        "semantic_eq",
    ] = "eq"
    value: Any

    @field_validator("field", mode="before")
    @classmethod
    def normalize_field(cls, value: Any) -> str:
        return normalize_token(value)

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: Any) -> str:
        return normalize_token(value)


class SemanticOrderBy(BaseModel):
    field: str
    direction: Literal["asc", "desc"] = "asc"

    @field_validator("field", mode="before")
    @classmethod
    def normalize_field(cls, value: Any) -> str:
        return normalize_token(value)

    @field_validator("direction", mode="before")
    @classmethod
    def normalize_direction(cls, value: Any) -> str:
        return normalize_token(value)


class SemanticSearchRequest(BaseModel):
    entity: Literal["ticket", "ticket_sla"]
    select: Optional[List[str]] = None
    where: Optional[List[SemanticFilterCondition]] = None
    include: Optional[List[str]] = None
    order_by: Optional[List[SemanticOrderBy]] = None
    limit: Optional[int] = Field(default=None, ge=1)

    @field_validator("entity", mode="before")
    @classmethod
    def normalize_entity(cls, value: Any) -> str:
        return normalize_token(value)

    @field_validator("select", mode="before")
    @classmethod
    def normalize_select(cls, value: Any) -> Any:
        if value is None:
            return value

        if isinstance(value, list):
            return [normalize_token(item) for item in value]

        return value

    @field_validator("include", mode="before")
    @classmethod
    def normalize_include(cls, value: Any) -> Any:
        if value is None:
            return value

        if isinstance(value, list):
            return [normalize_token(item) for item in value]

        return value


class SemanticSearchResponse(BaseModel):
    entity: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int


class SemanticCountResponse(BaseModel):
    entity: str
    count: int
    execution_time_ms: int


class CopilotTicketCountRequest(BaseModel):
    company_contains: Optional[str] = None
    summary_contains: Optional[str] = None
    summary_contains_all: Optional[List[str]] = None
    status: Optional[str] = None
    board_contains: Optional[str] = None
    owner_contains: Optional[str] = None
    date_entered_gte: Optional[str] = None
    date_entered_lte: Optional[str] = None
    last_updated_gte: Optional[str] = None
    last_updated_lte: Optional[str] = None


class CopilotSemanticCountJsonRequest(BaseModel):
    entity: Literal["ticket"] = "ticket"
    filters_json: str

    @field_validator("entity", mode="before")
    @classmethod
    def normalize_entity(cls, value: Any) -> str:
        return normalize_token(value)


class CopilotSemanticSearchJsonRequest(BaseModel):
    entity: Literal["ticket"] = "ticket"
    filters_json: Optional[str] = None
    select_json: Optional[str] = None
    order_by_json: Optional[str] = None
    limit: Optional[int] = Field(default=10, ge=1)

    @field_validator("entity", mode="before")
    @classmethod
    def normalize_entity(cls, value: Any) -> str:
        return normalize_token(value)


class CopilotSlaSearchJsonRequest(BaseModel):
    entity: Literal["ticket_sla"] = "ticket_sla"
    filters_json: Optional[str] = None
    select_json: Optional[str] = None
    order_by_json: Optional[str] = None
    limit: Optional[int] = Field(default=100, ge=1)

    @field_validator("entity", mode="before")
    @classmethod
    def normalize_entity(cls, value: Any) -> str:
        return normalize_token(value)


class CopilotTicketNotesJsonRequest(BaseModel):
    entity: Literal["ticket"] = "ticket"
    filters_json: str
    limit_tickets: int = Field(default=10, ge=1)
    limit_notes: int = Field(default=100, ge=1)
    include_internal: bool = True

    @field_validator("entity", mode="before")
    @classmethod
    def normalize_entity(cls, value: Any) -> str:
        return normalize_token(value)


class TicketNotesRequest(BaseModel):
    ticket_where: Optional[List[SemanticFilterCondition]] = None
    limit_tickets: int = Field(default=10, ge=1)
    limit_notes: int = Field(default=100, ge=1)
    include_internal: bool = True


class TicketNotesResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int