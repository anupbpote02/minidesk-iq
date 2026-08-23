from app.config import TICKET_CATEGORIES
from app.db import crud


def create_ticket(description: str, category: str, requester: str) -> dict:
    if category not in TICKET_CATEGORIES:
        category = "Other"
    ticket = crud.create_ticket(description=description, category=category, requester=requester)
    return {
        "status": "created",
        "ticket_id": ticket["id"],
        "category": ticket["category"],
        "ticket_status": ticket["status"],
    }
