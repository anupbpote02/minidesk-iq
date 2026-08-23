from app.db import crud


def approve_request(ticket_id: int, approver: str) -> dict:
    ticket = crud.get_ticket(ticket_id)
    if not ticket:
        return {"status": "error", "message": f"No ticket found with ID {ticket_id}."}

    updated = crud.update_ticket_status(ticket_id, status="in_progress", approver=approver)
    crud.log_audit(actor=approver, event_type="ticket_approved", detail=f"ticket #{ticket_id}")
    return {
        "status": "approved",
        "ticket_id": updated["id"],
        "ticket_status": updated["status"],
        "approver": updated["approver"],
    }
