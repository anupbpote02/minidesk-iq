from app.db import crud


def check_ticket_status(ticket_id: int) -> dict:
    ticket = crud.get_ticket(ticket_id)
    if not ticket:
        return {"status": "error", "message": f"No ticket found with ID {ticket_id}."}
    return {
        "status": "found",
        "ticket_id": ticket["id"],
        "description": ticket["description"],
        "category": ticket["category"],
        "ticket_status": ticket["status"],
        "requester": ticket["requester"],
        "created_at": ticket["created_at"],
        "resolved_at": ticket["resolved_at"],
    }
