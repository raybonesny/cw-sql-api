from app.schemas import (
    CopilotTicketCountRequest,
    SemanticFilterCondition,
    SemanticSearchRequest,
)


def build_semantic_count_request_from_copilot(
    request: CopilotTicketCountRequest,
) -> SemanticSearchRequest:
    where: list[SemanticFilterCondition] = []

    if request.company_contains:
        where.append(
            SemanticFilterCondition(
                field="company",
                operator="contains",
                value=request.company_contains,
            )
        )

    if request.summary_contains:
        where.append(
            SemanticFilterCondition(
                field="summary",
                operator="contains",
                value=request.summary_contains,
            )
        )

    if request.summary_contains_all:
        where.append(
            SemanticFilterCondition(
                field="summary",
                operator="contains_all",
                value=request.summary_contains_all,
            )
        )

    if request.status:
        where.append(
            SemanticFilterCondition(
                field="status",
                operator="semantic_eq",
                value=request.status,
            )
        )

    if request.board_contains:
        where.append(
            SemanticFilterCondition(
                field="board",
                operator="contains",
                value=request.board_contains,
            )
        )

    if request.owner_contains:
        where.append(
            SemanticFilterCondition(
                field="owner",
                operator="contains",
                value=request.owner_contains,
            )
        )

    if request.date_entered_gte:
        where.append(
            SemanticFilterCondition(
                field="date_entered",
                operator="gte",
                value=request.date_entered_gte,
            )
        )

    if request.date_entered_lte:
        where.append(
            SemanticFilterCondition(
                field="date_entered",
                operator="lte",
                value=request.date_entered_lte,
            )
        )

    if request.last_updated_gte:
        where.append(
            SemanticFilterCondition(
                field="last_updated",
                operator="gte",
                value=request.last_updated_gte,
            )
        )

    if request.last_updated_lte:
        where.append(
            SemanticFilterCondition(
                field="last_updated",
                operator="lte",
                value=request.last_updated_lte,
            )
        )

    return SemanticSearchRequest(
        entity="ticket",
        where=where,
    )