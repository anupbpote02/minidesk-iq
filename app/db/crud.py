from datetime import datetime, timezone
from typing import Any, Optional

from app.db.database import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------

def create_ticket(description: str, category: str, requester: str) -> dict[str, Any]:
    now = _now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tickets (description, category, status, requester, created_at)
            VALUES (?, ?, 'open', ?, ?)
            """,
            (description, category, requester, now),
        )
        ticket_id = cursor.lastrowid
    log_audit(actor=requester, event_type="ticket_created", detail=f"ticket #{ticket_id}: {description}")
    return get_ticket(ticket_id)


def get_ticket(ticket_id: int) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return dict(row) if row else None


def update_ticket_status(ticket_id: int, status: str, approver: Optional[str] = None) -> Optional[dict[str, Any]]:
    resolved_at = _now() if status == "resolved" else None
    with get_connection() as conn:
        if approver is not None:
            conn.execute(
                "UPDATE tickets SET status = ?, approver = ?, resolved_at = COALESCE(?, resolved_at) WHERE id = ?",
                (status, approver, resolved_at, ticket_id),
            )
        else:
            conn.execute(
                "UPDATE tickets SET status = ?, resolved_at = COALESCE(?, resolved_at) WHERE id = ?",
                (status, resolved_at, ticket_id),
            )
    return get_ticket(ticket_id)


def list_tickets(category: Optional[str] = None, status: Optional[str] = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM tickets WHERE 1=1"
    params: list[Any] = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Query logs
# ---------------------------------------------------------------------------

def log_query(
    user_query: str,
    action_taken: str,
    source: Optional[str],
    response: str,
    latency_ms: float,
    success: bool = True,
    is_knowledge_gap: bool = False,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO query_logs
                (timestamp, user_query, action_taken, source, response, latency_ms, success, is_knowledge_gap)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now(),
                user_query,
                action_taken,
                source,
                response,
                latency_ms,
                1 if success else 0,
                1 if is_knowledge_gap else 0,
            ),
        )
        return cursor.lastrowid


def list_query_logs(limit: int = 500) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM query_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def log_audit(actor: str, event_type: str, detail: str = "") -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO audit_log (timestamp, actor, event_type, detail) VALUES (?, ?, ?, ?)",
            (_now(), actor, event_type, detail),
        )
        return cursor.lastrowid


def list_audit_log(limit: int = 500) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
