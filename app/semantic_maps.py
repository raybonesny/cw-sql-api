from typing import Dict, List, Set

# These are generic / semantic buckets.
# IMPORTANT:
# We only use these when the incoming filter field is a GENERIC semantic field
# like "status" or "ticket_status".
#
# If the caller sends the explicit field "SR_Status.SR_Status",
# we DO NOT override or remap it.
STATUS_MAP: Dict[str, List[str]] = {
    "open": [
        "New",
        "In Progress",
        "Working Issue Now",
        "Waiting on Client",
        "Waiting on Vendor",
        "Waiting on Teammate",
        "Waiting on Parts",
        "Need Part",
        "On-Hold",
        "On Hold",
        "Assigned",
        "Engineering in Process",
        "Fix Ticket",
        "Waiting Client Response",
        "Waiting on 3rd Party",
        "Waiting on Approval",
        "Waiting Order",
        "Approval Needed",
        "Done Yet?",
        "Pre-Process",
        "Pending Closure",
        "Pending Closure No Contact",
        "Scheduling Required",
        "Scheduling Required - CS",
        "Scheduling Required - ST",
        "Scheduling in Progress",
        "Queue",
        "Queued",
        "Ready",
        "Ready to GO",
        "Client Responded",
        "Needs follow-up",
        "Needs Follow-Up",
        "Research Needed",
        "Working Issue Now",
    ],
    "scheduled": [
        "Scheduled",
        "Scheduled Remote",
        "Scheduled Onsite",
        "Scheduled Silent",
        "Scheduled with Client",
        "Scheduling Required",
        "Scheduling Required - CS",
        "Scheduling Required - ST",
        "Scheduling in Progress",
    ],
    "complete": [
        "Completed",
        "Completed~",
        "Completed upon Approval",
        "Completed Child Ticket",
        "Completed Child  Ticket",
        "Completed - Silent",
        "Completed upon Approval",
        "QC Completed",
        "Idea Implemented",
        "Completed Child Ticket",
    ],
    "closed": [
        "Closed",
        ">Closed",
        ">Closed~",
        ">Closed No Survey",
        ">Closed Send Survey",
        ">Closed Standard Survey",
        "Closed - Duplicate",
        "Closed - Insufficient Information",
        "Closed - Not a Fit",
        "Closed - Hired",
        "Closed--Accepted another position",
        "Closed - App Expired",
    ],
    "canceled": [
        "Canceled",
        "Cancelled",
        ">Canceled",
        ">Cancelled",
        "Class Canceled",
    ],
}

# Canonical explicit status names.
# These are only used to prevent semantic-mapping from overriding a real status
# when the caller is using a GENERIC semantic field and actually meant a real status.
#
# Example:
#   field = "status", value = "In Progress"  -> exact status match -> use eq "In Progress"
#   field = "status", value = "open"         -> semantic term       -> use in [...]
#
# NOTE:
# We intentionally include common actual values here, not every single status in the workbook.
ACTUAL_STATUS_CANONICAL: Dict[str, str] = {
    "new": "New",
    "open": "Open",
    "assigned": "Assigned",
    "in progress": "In Progress",
    "working issue now": "Working Issue Now",
    "waiting on client": "Waiting on Client",
    "waiting client response": "Waiting Client Response",
    "waiting on vendor": "Waiting on Vendor",
    "waiting on teammate": "Waiting on Teammate",
    "waiting on parts": "Waiting on Parts",
    "need part": "Need Part",
    "on-hold": "On-Hold",
    "on hold": "On Hold",
    "scheduled": "Scheduled",
    "scheduled remote": "Scheduled Remote",
    "scheduled onsite": "Scheduled Onsite",
    "scheduled silent": "Scheduled Silent",
    "scheduling required": "Scheduling Required",
    "completed": "Completed",
    "completed~": "Completed~",
    "completed upon approval": "Completed upon Approval",
    "completed child ticket": "Completed Child Ticket",
    "completed - silent": "Completed - Silent",
    "closed": "Closed",
    ">closed": ">Closed",
    "canceled": "Canceled",
    "cancelled": "Cancelled",
    ">canceled": ">Canceled",
    "fix ticket": "Fix Ticket",
    "engineering in process": "Engineering in Process",
    "research needed": "Research Needed",
    "done yet?": "Done Yet?",
    "approval needed": "Approval Needed",
    "pending closure": "Pending Closure",
    "pending closure no contact": "Pending Closure No Contact",
    "pre-process": "Pre-Process",
    "queue": "Queue",
    "queued": "Queued",
    "ready": "Ready",
}

# These are the GENERIC field names that should trigger semantic status handling.
# If the filter field is already explicit, like "SR_Status.Description", do NOT remap it.
SEMANTIC_STATUS_FIELDS: Set[str] = {
    "status",
    "ticket_status",
    "service_status",
    "status_group",
    "ticket_state",
}


# These are the GENERIC field names that should trigger semantic priority/urgency handling.
# ConnectWise Manage tickets store this as SR_Service.SR_Urgency_RecID and join to SR_Urgency.
SEMANTIC_PRIORITY_FIELDS: Set[str] = {
    "priority",
    "ticket_priority",
    "service_priority",
    "urgency",
    "ticket_urgency",
    "service_urgency",
    "impact",
}


# Your current SR_Urgency values:
#   2  = Priority 1 - Emergency 4 Hour Resolution = Critical
#   1  = Priority 2 - Quick 1 Day Resolution      = High
#   4  = Priority 3 - Normal 2 Day Resolution     = Medium
#   13 = Priority 4 - 5 Business Day Resolution   = Low
#   3  = Priority 5 - Extended 1 Month Resolution
#   10 = Some Time
#   6  = Next Visit
#
# We resolve these to SR_Urgency.SR_Urgency_RecID instead of Description so the
# query is exact and resilient to description wording.
PRIORITY_CANONICAL: Dict[str, int] = {
    "p1": 2,
    "p 1": 2,
    "priority 1": 2,
    "priority one": 2,
    "critical": 2,
    "emergency": 2,
    "urgent": 2,

    "p2": 1,
    "p 2": 1,
    "priority 2": 1,
    "priority two": 1,
    "high": 1,
    "quick": 1,

    "p3": 4,
    "p 3": 4,
    "priority 3": 4,
    "priority three": 4,
    "medium": 4,
    "normal": 4,

    "p4": 13,
    "p 4": 13,
    "priority 4": 13,
    "priority four": 13,
    "low": 13,

    "p5": 3,
    "p 5": 3,
    "priority 5": 3,
    "priority five": 3,
    "extended": 3,

    "some time": 10,
    "sometime": 10,

    "next visit": 6,
}


def resolve_status_filter(value: str) -> dict:
    raw_value = str(value).strip()
    normalized = raw_value.lower()

    # Case 1: exact real status
    if normalized in ACTUAL_STATUS_CANONICAL:
        return {
            "field": "SR_Status.Description",
            "operator": "eq",
            "value": ACTUAL_STATUS_CANONICAL[normalized],
        }

    # Case 2: semantic group
    if normalized in STATUS_MAP:
        return {
            "field": "SR_Status.Description",
            "operator": "in",
            "value": STATUS_MAP[normalized],
        }

    # Case 3: fallback
    return {
        "field": "SR_Status.Description",
        "operator": "contains",
        "value": raw_value,
    }


def resolve_priority_filter(value: str) -> dict:
    raw_value = str(value).strip()
    normalized = raw_value.lower()

    if normalized in PRIORITY_CANONICAL:
        return {
            "field": "SR_Urgency.SR_Urgency_RecID",
            "operator": "eq",
            "value": PRIORITY_CANONICAL[normalized],
        }

    return {
        "field": "SR_Urgency.Description",
        "operator": "contains",
        "value": raw_value,
    }