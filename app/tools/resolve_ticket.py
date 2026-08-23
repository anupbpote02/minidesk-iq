from app.db import crud


def resolve_ticket(ticket_id: int, resolver: str) -> dict:
    ticket = crud.get_ticket(ticket_id)
    if not ticket:
        return {"status": "error", "message": f"No ticket found with ID {ticket_id}."}

    updated = crud.update_ticket_status(ticket_id, status="resolved", approver=resolver)
    crud.log_audit(
        actor=resolver,
        event_type="ticket_closed",
        detail=f"ticket #{ticket_id}: resolved by {resolver}",
    )
    return {
        "status": "resolved",
        "ticket_id": updated["id"],
        "ticket_status": updated["status"],
        "resolved_at": updated["resolved_at"],
        "resolver": resolver,
    }
