"""OpenAI function-calling (tool) schemas for MiniDesk IQ."""

from app.config import TICKET_CATEGORIES

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": (
                "Create a new IT service desk ticket on behalf of the employee. "
                "Use this when the employee wants to request something (VPN access, "
                "a password reset that self-service can't fix, new hardware, etc.) "
                "or report a problem that requires human follow-up."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "A clear, concise description of the request or issue.",
                    },
                    "category": {
                        "type": "string",
                        "enum": TICKET_CATEGORIES,
                        "description": "The category that best matches the request.",
                    },
                    "requester": {
                        "type": "string",
                        "description": "Name or email of the employee making the request.",
                    },
                },
                "required": ["description", "category", "requester"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_ticket_status",
            "description": "Look up the current status of an existing ticket by its ticket ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The numeric ID of the ticket to look up.",
                    },
                },
                "required": ["ticket_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "approve_request",
            "description": (
                "Approve a pending ticket/request (e.g., a manager or admin approving "
                "a VPN access or hardware request). Moves the ticket to in_progress."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The numeric ID of the ticket to approve.",
                    },
                    "approver": {
                        "type": "string",
                        "description": "Name or email of the person approving the request.",
                    },
                },
                "required": ["ticket_id", "approver"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resolve_ticket",
            "description": (
                "Resolve/close an existing ticket, setting its status to 'resolved'. "
                "This is restricted to the admin account — only call this when the "
                "person making the request is the logged-in admin. If a non-admin "
                "employee asks to close or resolve a ticket, do not call this tool; "
                "politely explain that only an admin can close tickets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The numeric ID of the ticket to resolve.",
                    },
                    "resolver": {
                        "type": "string",
                        "description": "Name or email of the person resolving the ticket.",
                    },
                },
                "required": ["ticket_id", "resolver"],
            },
        },
    },
]
