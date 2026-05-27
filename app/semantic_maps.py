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
# If the filter field is already explicit, like "SR_Status.SR_Status", do NOT remap it.
SEMANTIC_STATUS_FIELDS: Set[str] = {
    "status",
    "ticket_status",
    "service_status",
    "status_group",
    "ticket_state",
}



def resolve_status_filter(value: str) -> dict:
    raw_value = str(value).strip()
    normalized = raw_value.lower()

    # ✅ Case 1: exact real status
    if normalized in ACTUAL_STATUS_CANONICAL:
        return {
            "field": "SR_Status.Description",
            "operator": "eq",
            "value": ACTUAL_STATUS_CANONICAL[normalized],
        }

    # ✅ Case 2: semantic group
    if normalized in STATUS_MAP:
        return {
            "field": "SR_Status.Description",
            "operator": "in",
            "value": STATUS_MAP[normalized],
        }

    # ✅ Case 3: fallback
    return {
        "field": "SR_Status.Description",
        "operator": "contains",
        "value": raw_value,
    }
