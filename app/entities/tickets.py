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
        "owner.name",
        "date_entered",
        "last_updated",
        "is_closed",
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
        "is_closed": FieldMapping(
            sql_expression="ticket.IsClosed_Flag",
            output_name="is_closed",
        ),
        "record_type": FieldMapping(
            sql_expression="ticket.Rec_Type",
            output_name="record_type",
        ),
        "date_entered": FieldMapping(
            sql_expression="ticket.Date_Entered",
            output_name="date_entered",
        ),
        "date_entered_utc": FieldMapping(
            sql_expression="ticket.Date_Entered_UTC",
            output_name="date_entered_utc",
        ),
        "date_required": FieldMapping(
            sql_expression="ticket.Date_Req",
            output_name="date_required",
        ),
        "last_updated": FieldMapping(
            sql_expression="ticket.Last_Update",
            output_name="last_updated",
        ),
        "last_updated_utc": FieldMapping(
            sql_expression="ticket.Last_Update_UTC",
            output_name="last_updated_utc",
        ),
        "closed_date": FieldMapping(
            sql_expression="ticket.Date_Closed",
            output_name="closed_date",
        ),
        "closed_date_utc": FieldMapping(
            sql_expression="ticket.Date_Closed_UTC",
            output_name="closed_date_utc",
        ),
        "entered_by": FieldMapping(
            sql_expression="ticket.Entered_By",
            output_name="entered_by",
        ),
        "updated_by": FieldMapping(
            sql_expression="ticket.Updated_By",
            output_name="updated_by",
        ),
        "closed_by": FieldMapping(
            sql_expression="ticket.Closed_By",
            output_name="closed_by",
        ),
        "po_number": FieldMapping(
            sql_expression="ticket.PO_Number",
            output_name="po_number",
        ),
        "reference": FieldMapping(
            sql_expression="ticket.Reference",
            output_name="reference",
        ),
        "site_name": FieldMapping(
            sql_expression="ticket.Site_Name",
            output_name="site_name",
        ),
        "external_xref": FieldMapping(
            sql_expression="ticket.External_Xref",
            output_name="external_xref",
        ),
        "parent.id": FieldMapping(
            sql_expression="ticket.Parent_RecID",
            output_name="parent_id",
        ),
        "agreement.id": FieldMapping(
            sql_expression="ticket.AGR_Header_RecID",
            output_name="agreement_id",
        ),
        "project_phase.id": FieldMapping(
            sql_expression="ticket.PM_Phase_RecID",
            output_name="project_phase_id",
        ),
        "company.id": FieldMapping(
            sql_expression="company.Company_RecID",
            output_name="company_id",
            required_include="company",
        ),
        "company.identifier": FieldMapping(
            sql_expression="company.Company_ID",
            output_name="company_identifier",
            required_include="company",
        ),
        "company.name": FieldMapping(
            sql_expression="company.Company_Name",
            output_name="company_name",
            required_include="company",
        ),
        "contact.id": FieldMapping(
            sql_expression="contact.Contact_RecID",
            output_name="contact_id",
            required_include="contact",
        ),
        "contact.first_name": FieldMapping(
            sql_expression="contact.First_Name",
            output_name="contact_first_name",
            required_include="contact",
        ),
        "contact.last_name": FieldMapping(
            sql_expression="contact.Last_Name",
            output_name="contact_last_name",
            required_include="contact",
        ),
        "contact.name": FieldMapping(
            sql_expression="LTRIM(RTRIM(CONCAT(contact.First_Name, ' ', contact.Last_Name)))",
            output_name="contact_name",
            required_include="contact",
        ),
        "contact.email": FieldMapping(
            sql_expression="contact.Email_Address",
            output_name="contact_email",
            required_include="contact",
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
        "status.closed_flag": FieldMapping(
            sql_expression="status.Closed_Flag",
            output_name="status_closed_flag",
            required_include="status",
        ),
        "status.resolved_flag": FieldMapping(
            sql_expression="status.Resolved_Flag",
            output_name="status_resolved_flag",
            required_include="status",
        ),
        "status.inactive_flag": FieldMapping(
            sql_expression="status.Inactive_Flag",
            output_name="status_inactive_flag",
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
        "owner.id": FieldMapping(
            sql_expression="owner.Member_RecID",
            output_name="owner_id",
            required_include="owner",
        ),
        "owner.identifier": FieldMapping(
            sql_expression="owner.Member_ID",
            output_name="owner_identifier",
            required_include="owner",
        ),
        "owner.name": FieldMapping(
            sql_expression="LTRIM(RTRIM(CONCAT(owner.First_Name, ' ', owner.Last_Name)))",
            output_name="owner_name",
            required_include="owner",
        ),
        "owner.email": FieldMapping(
            sql_expression="owner.Email_Address",
            output_name="owner_email",
            required_include="owner",
        ),
        "type.id": FieldMapping(
            sql_expression="ticket_type.SR_Type_RecID",
            output_name="type_id",
            required_include="type",
        ),
        "type.name": FieldMapping(
            sql_expression="ticket_type.Description",
            output_name="type_name",
            required_include="type",
        ),
        "subtype.id": FieldMapping(
            sql_expression="subtype.SR_SubType_RecID",
            output_name="subtype_id",
            required_include="subtype",
        ),
        "subtype.name": FieldMapping(
            sql_expression="subtype.Description",
            output_name="subtype_name",
            required_include="subtype",
        ),
        "item.id": FieldMapping(
            sql_expression="item.SR_SubTypeItem_RecID",
            output_name="item_id",
            required_include="item",
        ),
        "item.name": FieldMapping(
            sql_expression="item.Description",
            output_name="item_name",
            required_include="item",
        ),
        "urgency.id": FieldMapping(
            sql_expression="urgency.SR_Urgency_RecID",
            output_name="urgency_id",
            required_include="urgency",
        ),
        "urgency.name": FieldMapping(
            sql_expression="urgency.Description",
            output_name="urgency_name",
            required_include="urgency",
        ),
        "urgency.level": FieldMapping(
            sql_expression="urgency.Urgency_Level",
            output_name="urgency_level",
            required_include="urgency",
        ),
        "impact.id": FieldMapping(
            sql_expression="impact.SR_Impact_RecID",
            output_name="impact_id",
            required_include="impact",
        ),
        "impact.name": FieldMapping(
            sql_expression="impact.SR_Impact_Name",
            output_name="impact_name",
            required_include="impact",
        ),
        "severity.id": FieldMapping(
            sql_expression="severity.SR_Severity_RecID",
            output_name="severity_id",
            required_include="severity",
        ),
        "severity.name": FieldMapping(
            sql_expression="severity.SR_Severity_Name",
            output_name="severity_name",
            required_include="severity",
        ),
        "source.id": FieldMapping(
            sql_expression="source.SR_Source_RecID",
            output_name="source_id",
            required_include="source",
        ),
        "source.name": FieldMapping(
            sql_expression="source.Description",
            output_name="source_name",
            required_include="source",
        ),
        "team.id": FieldMapping(
            sql_expression="team.SR_Team_RecID",
            output_name="team_id",
            required_include="team",
        ),
        "team.name": FieldMapping(
            sql_expression="team.Description",
            output_name="team_name",
            required_include="team",
        ),
    },
    includes={
        "company": IncludeMapping(
            join_sql=(
                "LEFT JOIN Company company "
                "ON ticket.Company_RecID = company.Company_RecID"
            ),
        ),
        "contact": IncludeMapping(
            join_sql=(
                "LEFT JOIN Contact contact "
                "ON ticket.Contact_RecID = contact.Contact_RecID"
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
        "owner": IncludeMapping(
            join_sql=(
                "LEFT JOIN Member owner "
                "ON ticket.Ticket_Owner_RecID = owner.Member_RecID"
            ),
        ),
        "type": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_Type ticket_type "
                "ON ticket.SR_Type_RecID = ticket_type.SR_Type_RecID"
            ),
        ),
        "subtype": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_SubType subtype "
                "ON ticket.SR_SubType_RecID = subtype.SR_SubType_RecID"
            ),
        ),
        "item": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_SubTypeItem item "
                "ON ticket.SR_SubTypeItem_RecID = item.SR_SubTypeItem_RecID"
            ),
        ),
        "urgency": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_Urgency urgency "
                "ON ticket.SR_Urgency_RecID = urgency.SR_Urgency_RecID"
            ),
        ),
        "impact": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_Impact impact "
                "ON ticket.SR_Impact_RecID = impact.SR_Impact_RecID"
            ),
        ),
        "severity": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_Severity severity "
                "ON ticket.SR_Severity_RecID = severity.SR_Severity_RecID"
            ),
        ),
        "source": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_Source source "
                "ON ticket.SR_Source_RecID = source.SR_Source_RecID"
            ),
        ),
        "team": IncludeMapping(
            join_sql=(
                "LEFT JOIN SR_Team team "
                "ON ticket.SR_Team_RecID = team.SR_Team_RecID"
            ),
        ),
    },
)


ENTITY_REGISTRY = {
    "ticket": TICKET_ENTITY,
}

TICKET_SLA_ENTITY = EntityMapping(
    name="ticket_sla",
    base_table="v_rpt_Service_SLA",
    base_alias="sla",
    default_select=[
        "ticket_number",
        "summary",
        "company.name",
        "company.type",
        "team_bucket",
        "board",
        "status",
        "priority",
        "sla.name",
        "sla.status",
        "sla.response_due_at",
        "sla.resplan_due_at",
        "sla.resolution_due_at",
        "sla.minutes_to_response",
        "sla.minutes_to_resplan",
        "sla.minutes_to_resolution",
        "sla.response_state",
        "sla.resplan_state",
        "sla.resolution_state",
        "is_closed",
    ],
    fields={
        "ticket_number": FieldMapping(sql_expression="sla.SR_Service_RecID", output_name="ticket_number"),
        "id": FieldMapping(sql_expression="sla.SR_Service_RecID", output_name="ticket_number"),
        "ticket_nbr": FieldMapping(sql_expression="ticket.TicketNbr", output_name="ticket_nbr", required_include="ticket"),
        "summary": FieldMapping(sql_expression="ticket.Summary", output_name="summary", required_include="ticket"),
        "company.id": FieldMapping(sql_expression="ticket.company_recid", output_name="company_id", required_include="ticket"),
        "company.name": FieldMapping(sql_expression="ticket.company_name", output_name="company_name", required_include="ticket"),
        "company.type": FieldMapping(sql_expression="company.Company_Type_Desc", output_name="company_type", required_include="company"),
        "company.market": FieldMapping(sql_expression="company.Market_Desc", output_name="market", required_include="company"),
        "territory": FieldMapping(sql_expression="ticket.Territory", output_name="territory", required_include="ticket"),
        "territory_manager": FieldMapping(sql_expression="ticket.Territory_Manager", output_name="territory_manager", required_include="ticket"),
        "team_name": FieldMapping(sql_expression="ticket.team_name", output_name="team_name", required_include="ticket"),
        "team_bucket": FieldMapping(
            sql_expression=(
                "CASE "
                "WHEN company.Company_Type_Desc LIKE '%Client MST2%' THEN 'MST2' "
                "WHEN company.Company_Type_Desc LIKE '%Client MST4%' THEN 'MST4' "
                "WHEN company.Company_Type_Desc LIKE '%Client MST5%' THEN 'MST5' "
                "WHEN company.Company_Type_Desc LIKE '%Client TST1%' THEN 'TST1' "
                "WHEN company.Company_Type_Desc LIKE '%Internal%' THEN 'Internal' "
                "ELSE 'Unmapped' END"
            ),
            output_name="team_bucket",
            required_include="company",
        ),
        "board": FieldMapping(sql_expression="ticket.Board_Name", output_name="board", required_include="ticket"),
        "board.name": FieldMapping(sql_expression="ticket.Board_Name", output_name="board", required_include="ticket"),
        "status": FieldMapping(sql_expression="ticket.status_description", output_name="status", required_include="ticket"),
        "status.name": FieldMapping(sql_expression="ticket.status_description", output_name="status", required_include="ticket"),
        "priority": FieldMapping(sql_expression="ticket.Priority_Description", output_name="priority", required_include="ticket"),
        "urgency": FieldMapping(sql_expression="ticket.Urgency", output_name="urgency", required_include="ticket"),
        "assigned_technicians": FieldMapping(sql_expression="ticket.resource_list", output_name="assigned_technicians", required_include="ticket"),
        "ticket.owner_fullname": FieldMapping(
            sql_expression="LTRIM(RTRIM(ISNULL(ticket.Ticket_Owner_First_Name, '') + ' ' + ISNULL(ticket.Ticket_Owner_Last_Name, '')))",
            output_name="ticket_owner_fullname",
            required_include="ticket",
        ),
        "owner.name": FieldMapping(
            sql_expression="LTRIM(RTRIM(ISNULL(ticket.Ticket_Owner_First_Name, '') + ' ' + ISNULL(ticket.Ticket_Owner_Last_Name, '')))",
            output_name="ticket_owner_fullname",
            required_include="ticket",
        ),
        "is_closed": FieldMapping(sql_expression="sla.Closed_Flag", output_name="is_closed"),
        "sla.name": FieldMapping(sql_expression="sla.SLA_Name", output_name="sla_name"),
        "sla.status": FieldMapping(sql_expression="sla.SLA_Status_Text", output_name="sla_status"),
        "sla.response_due_at": FieldMapping(sql_expression="sla.Expected_Responded_Expiration_Date_UTC", output_name="sla_response_due_at"),
        "sla.resplan_due_at": FieldMapping(sql_expression="sla.Expected_Resplan_Expiration_Date_UTC", output_name="sla_resplan_due_at"),
        "sla.resolution_due_at": FieldMapping(sql_expression="sla.Expected_Resolution_Expiration_Date_UTC", output_name="sla_resolution_due_at"),
        "sla.next_due_at": FieldMapping(sql_expression="sla.Min_Expected_Expiration_Date_UTC", output_name="sla_next_due_at"),
        "sla.minutes_to_response": FieldMapping(sql_expression="DATEDIFF(minute, GETUTCDATE(), sla.Expected_Responded_Expiration_Date_UTC)", output_name="sla_minutes_to_response"),
        "sla.minutes_to_resplan": FieldMapping(sql_expression="DATEDIFF(minute, GETUTCDATE(), sla.Expected_Resplan_Expiration_Date_UTC)", output_name="sla_minutes_to_resplan"),
        "sla.minutes_to_resolution": FieldMapping(sql_expression="DATEDIFF(minute, GETUTCDATE(), sla.Expected_Resolution_Expiration_Date_UTC)", output_name="sla_minutes_to_resolution"),
        "sla.response_state": FieldMapping(
            sql_expression=(
                "CASE "
                "WHEN sla.Date_Responded_UTC IS NOT NULL THEN 'Met' "
                "WHEN sla.Expected_Responded_Expiration_Date_UTC IS NULL THEN 'Waiting' "
                "WHEN GETUTCDATE() > sla.Expected_Responded_Expiration_Date_UTC THEN 'Breached' "
                "ELSE 'Open' END"
            ),
            output_name="sla_response_state",
        ),
        "sla.resplan_state": FieldMapping(
            sql_expression=(
                "CASE "
                "WHEN sla.Date_Resplan_UTC IS NOT NULL THEN 'Met' "
                "WHEN sla.Expected_Resplan_Expiration_Date_UTC IS NULL THEN 'Waiting' "
                "WHEN GETUTCDATE() > sla.Expected_Resplan_Expiration_Date_UTC THEN 'Breached' "
                "ELSE 'Open' END"
            ),
            output_name="sla_resplan_state",
        ),
        "sla.resolution_state": FieldMapping(
            sql_expression=(
                "CASE "
                "WHEN sla.Date_Resolved_UTC IS NOT NULL THEN 'Met' "
                "WHEN sla.Expected_Resolution_Expiration_Date_UTC IS NULL THEN 'Waiting' "
                "WHEN GETUTCDATE() > sla.Expected_Resolution_Expiration_Date_UTC THEN 'Breached' "
                "ELSE 'Open' END"
            ),
            output_name="sla_resolution_state",
        ),
        "sla.responded_at": FieldMapping(sql_expression="sla.Date_Responded_UTC", output_name="sla_responded_at"),
        "sla.resplan_at": FieldMapping(sql_expression="sla.Date_Resplan_UTC", output_name="sla_resplan_at"),
        "sla.resolved_at": FieldMapping(sql_expression="sla.Date_Resolved_UTC", output_name="sla_resolved_at"),
        "sla.responded_minutes": FieldMapping(sql_expression="sla.Responded_Minutes", output_name="sla_responded_minutes"),
        "sla.resplan_minutes": FieldMapping(sql_expression="sla.Resplan_Minutes", output_name="sla_resplan_minutes"),
        "sla.resolved_minutes": FieldMapping(sql_expression="sla.Resolved_Minutes", output_name="sla_resolved_minutes"),
        "sla.minutes_waiting": FieldMapping(sql_expression="sla.Minutes_Waiting", output_name="sla_minutes_waiting"),
        "last_updated_utc": FieldMapping(sql_expression="sla.Last_Update_UTC", output_name="last_updated_utc"),
    },
    includes={
        "ticket": IncludeMapping(
            join_sql=(
                "INNER JOIN v_rpt_Service ticket "
                "ON ticket.SR_Service_RecID = sla.SR_Service_RecID"
            ),
        ),
        "company": IncludeMapping(
            join_sql=(
                "INNER JOIN v_rpt_Service ticket "
                "ON ticket.SR_Service_RecID = sla.SR_Service_RecID "
                "LEFT JOIN v_rpt_Company company "
                "ON company.Company_RecID = ticket.company_recid"
            ),
        ),
    },
)


ENTITY_REGISTRY["ticket_sla"] = TICKET_SLA_ENTITY
