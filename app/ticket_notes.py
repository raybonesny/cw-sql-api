import time
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel
from sqlalchemy import text

from app.database import get_engine
from app.entities.tickets import ENTITY_REGISTRY
from app.schemas import TicketNotesRequest, TicketNotesResponse
from app.semantic_search import (
    SemanticSearchError,
    _build_joins,
    _build_where,
    _normalize_sql_whitespace,
)


class TicketNotesSqlPreview(BaseModel):
    sql: str
    params: Dict[str, Any]
    columns: List[str]


TICKET_NOTES_COLUMNS = [
    "ticket_id",
    "ticket_summary",
    "note_id",
    "note_type",
    "note_text",
    "problem_flag",
    "internal_analysis_flag",
    "resolution_flag",
    "issue_flag",
    "member_id",
    "member_name",
    "contact_name",
    "date_entered_utc",
    "entered_by",
    "last_update_utc",
    "updated_by",
    "sort_by_date",
    "original_author",
]


def execute_ticket_notes_search(request: TicketNotesRequest) -> TicketNotesResponse:
    start_time = time.perf_counter()

    preview = build_ticket_notes_sql_preview(request)

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(preview.sql), preview.params)
        rows = [dict(row._mapping) for row in result]

    execution_time_ms = int((time.perf_counter() - start_time) * 1000)

    return TicketNotesResponse(
        columns=preview.columns,
        rows=rows,
        row_count=len(rows),
        execution_time_ms=execution_time_ms,
    )


def build_ticket_notes_sql_preview(request: TicketNotesRequest) -> TicketNotesSqlPreview:
    entity = ENTITY_REGISTRY.get("ticket")
    if entity is None:
        raise SemanticSearchError("Ticket entity mapping is not registered.")

    ticket_where_sql, params, required_includes = _build_where(
        entity,
        request.ticket_where or [],
    )

    joins_sql = _build_joins(entity, required_includes)

    limit_tickets = request.limit_tickets
    limit_notes = request.limit_notes

    if limit_tickets <= 0:
        raise SemanticSearchError("limit_tickets must be greater than zero.")

    if limit_notes <= 0:
        raise SemanticSearchError("limit_notes must be greater than zero.")

    params["limit_tickets"] = limit_tickets
    params["limit_notes"] = limit_notes

    internal_filter_sql = ""
    if not request.include_internal:
        internal_filter_sql = (
            "AND ISNULL(notes.InternalAnalysis_Flag, 0) = 0 "
            "AND ISNULL(notes.Internal_Member_Flag, 0) = 0"
        )

    sql = f"""
        WITH matching_tickets AS (
            SELECT TOP (:limit_tickets)
                ticket.SR_Service_RecID
            FROM {entity.base_table} {entity.base_alias}
            {joins_sql}
            {ticket_where_sql}
            ORDER BY ticket.Last_Update DESC
        )
        SELECT TOP (:limit_notes)
            notes.SR_Service_RecID AS ticket_id,
            notes.Summary AS ticket_summary,
            notes.ID AS note_id,
            notes.Note_Type AS note_type,
            notes.Text_Markdown AS note_text,
            notes.Problem_Flag AS problem_flag,
            notes.InternalAnalysis_Flag AS internal_analysis_flag,
            notes.Resolution_Flag AS resolution_flag,
            notes.Issue_Flag AS issue_flag,
            notes.Member_ID AS member_id,
            notes.Member_Name AS member_name,
            notes.Contact_Name AS contact_name,
            notes.Date_Entered_UTC AS date_entered_utc,
            notes.Entered_By AS entered_by,
            notes.Last_Update_UTC AS last_update_utc,
            notes.Updated_By AS updated_by,
            notes.SortByDate AS sort_by_date,
            notes.Original_Author AS original_author
        FROM v_api_collection_service_ticket_note notes
        INNER JOIN matching_tickets mt
            ON notes.SR_Service_RecID = mt.SR_Service_RecID
        WHERE
            notes.Text_Markdown IS NOT NULL
            {internal_filter_sql}
        ORDER BY
            notes.SortByDate DESC,
            notes.Last_Update_UTC DESC
    """

    return TicketNotesSqlPreview(
        sql=_normalize_sql_whitespace(sql),
        params=params,
        columns=TICKET_NOTES_COLUMNS,
    )