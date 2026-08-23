"""Core agent orchestration: decides between RAG, tool calls, or both, and logs every interaction."""

import json
import time
from typing import Any, Optional

from openai import OpenAI

from app.config import ADMIN_EMAIL, CHAT_MODEL, OPENAI_API_KEY, RETRIEVAL_SIMILARITY_THRESHOLD
from app.db import crud
from app.rag.retrieve import best_match_above_threshold, format_context, retrieve
from app.tools.approve_request import approve_request
from app.tools.check_ticket_status import check_ticket_status
from app.tools.create_ticket import create_ticket
from app.tools.resolve_ticket import resolve_ticket
from app.tools.schemas import TOOL_SCHEMAS

_client = OpenAI(api_key=OPENAI_API_KEY)

TOOL_IMPLEMENTATIONS = {
    "create_ticket": create_ticket,
    "check_ticket_status": check_ticket_status,
    "approve_request": approve_request,
    "resolve_ticket": resolve_ticket,
}

SYSTEM_PROMPT = """You are MiniDesk IQ, an agentic IT service desk copilot for employees.

You have two ways to help:
1. Answer using the IT/HR policy knowledge base context provided to you (VPN access,
   password reset, hardware requests, remote work, expense reimbursement).
2. Call a tool to create a ticket, check a ticket's status, approve a request, or
   resolve/close a ticket.

Rules:
- If the provided knowledge base context answers the question, answer clearly and
  concisely, and cite the source document name(s) you used.
- If the context does NOT contain a good answer AND the question is not something a
  tool can resolve, say plainly that this isn't something you have policy information
  on and that it's been logged for the team to review. Do not attempt to answer general
  knowledge, personal, or off-topic questions from your own knowledge — MiniDesk IQ only
  answers IT/HR policy questions and handles service desk requests.
- If the employee is asking to file a request, report an issue, check on an existing
  ticket, or approve something, use the appropriate tool.
- If someone asks to resolve or close a ticket, use the resolve_ticket tool.
  Closing tickets is restricted to the admin account. If the tool result says the
  requester doesn't have permission, tell the employee plainly that only an admin
  can close tickets and that they should contact an admin — do not attempt the
  action again or work around it.
- You may both answer from context AND call a tool in the same turn if the request
  calls for it (e.g., explaining the VPN policy and also filing a VPN access ticket).
- Keep responses concise and professional, like a helpful IT colleague.
"""


def _run_tool_call(tool_call, requester: str) -> dict[str, Any]:
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError:
        args = {}

    if name == "resolve_ticket":
        if requester != ADMIN_EMAIL:
            return {
                "status": "error",
                "message": "Only an admin can close tickets. Please contact an admin for help.",
            }
        # The resolver identity must come from the authenticated session, not the
        # model's tool-call arguments, so the audit trail can't be spoofed.
        args["resolver"] = "admin"

    fn = TOOL_IMPLEMENTATIONS.get(name)
    if fn is None:
        return {"status": "error", "message": f"Unknown tool: {name}"}
    return fn(**args)


def handle_message(user_message: str, requester: str = "employee") -> dict[str, Any]:
    """Main agent entrypoint. Returns the assistant response plus metadata about
    what action was taken, for logging and UI display."""
    start = time.time()

    retrieved_chunks = retrieve(user_message)
    has_good_match = best_match_above_threshold(retrieved_chunks, RETRIEVAL_SIMILARITY_THRESHOLD)
    context_text = format_context(retrieved_chunks) if retrieved_chunks else ""

    context_note = (
        f"Relevant knowledge base context (top matches):\n\n{context_text}"
        if has_good_match
        else (
            "No sufficiently relevant knowledge base context was found for this query. "
            "If the employee is asking a policy question, be honest that you don't have "
            "a confident answer rather than guessing."
        )
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_note},
        {"role": "user", "content": f"Employee ({requester}) says: {user_message}"},
    ]

    response = _client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
    )

    choice = response.choices[0]
    tool_calls = choice.message.tool_calls or []

    action_taken = "rag"
    tool_names: list[str] = []
    tool_results: list[dict[str, Any]] = []

    if tool_calls:
        action_taken = "both" if has_good_match else "tool"
        messages.append(choice.message)

        for tool_call in tool_calls:
            result = _run_tool_call(tool_call, requester)
            tool_names.append(tool_call.function.name)
            tool_results.append(result)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

        follow_up = _client.chat.completions.create(model=CHAT_MODEL, messages=messages)
        final_text = follow_up.choices[0].message.content or ""
    else:
        final_text = choice.message.content or ""

    latency_ms = (time.time() - start) * 1000

    is_knowledge_gap = action_taken == "rag" and not has_good_match

    sources = sorted({c.source for c in retrieved_chunks}) if has_good_match else []
    source_label = ", ".join(sources) if sources else (", ".join(tool_names) if tool_names else None)

    crud.log_query(
        user_query=user_message,
        action_taken=action_taken,
        source=source_label,
        response=final_text,
        latency_ms=latency_ms,
        success=True,
        is_knowledge_gap=is_knowledge_gap,
    )

    return {
        "response": final_text,
        "action_taken": action_taken,
        "sources": sources,
        "tools_called": tool_names,
        "tool_results": tool_results,
        "is_knowledge_gap": is_knowledge_gap,
        "latency_ms": latency_ms,
    }
