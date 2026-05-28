from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FieldMapping:
    sql_expression: str
    output_name: str
    required_include: Optional[str] = None


@dataclass(frozen=True)
class IncludeMapping:
    join_sql: str


@dataclass(frozen=True)
class EntityMapping:
    name: str
    base_table: str
    base_alias: str
    default_select: List[str]
    fields: Dict[str, FieldMapping]
    includes: Dict[str, IncludeMapping]


TICKET_ENTITY = EntityMapping(
    name="ticket",
    base_table="SR_Service",
    base_alias="ticket",
    default_select=[
        "id",
        "summary",
        "company.name",
        "status.name",
        "board.name",
        "date_entered",
        "last_updated",
    ],
    fields={
        "id": FieldMapping(
            sql_expression="ticket.SR_Service_RecID",
            output_name="id",
        ),
        "summary": FieldMapping(
            sql_expression="ticket.Summary",
            output_name="summary",
        ),
        "company.id": FieldMapping(
            sql_expression="company.Company_RecID",
            output_name="company_id",
            required_include="company",
        ),
        "company.name": FieldMapping(
            sql_expression="company.Company_Name",
            output_name="company_name",
            required_include="company",
        ),
        "status.id": FieldMapping(
            sql_expression="status.SR_Status_RecID",
            output_name="status_id",
            required_include="status",
        ),
        "status.name": FieldMapping(
            sql_expression="status.Description",
            output_name="status_name",
            required_include="status",
        ),
        "board.id": FieldMapping(
            sql_expression="board.SR_Board_RecID",
            output_name="board_id",
            required_include="board",
        ),
        "board.name": FieldMapping(
            sql_expression="board.Board_Name",
            output_name="board_name",
            required_include="board",
        ),
        "date_entered": FieldMapping(
            sql_expression="ticket.Date_Entered",
            output_name="date_entered",
        ),
        "last_updated": FieldMapping(
            sql_expression="ticket.Last_Update",
            output_name="last_updated",
        ),
        "closed_date": FieldMapping(
            sql_expression="ticket.Date_Closed",
            output_name="closed_date",
        ),
    },
    includes={
        "company": IncludeMapping(
            join_sql=(
                "LEFT JOIN Company company "
                "ON ticket.Company_RecID = company.Company_RecID"
            ),
        ),
        "status": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_Status status "
                "ON ticket.SR_Status_RecID = status.SR_Status_RecID"
            ),
        ),
        "board": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_Board board "
                "ON ticket.SR_Board_RecID = board.SR_Board_RecID"
            ),
        ),
    },
)


ENTITY_REGISTRY = {
    "ticket": TICKET_ENTITY,
}