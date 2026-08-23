import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.agent import handle_message
from app.db import crud
from app.db.database import init_db
from app.rag.ingest import (
    delete_document,
    extract_text_from_upload,
    get_chroma_client,
    get_or_create_collection,
    ingest_policies,
    save_policy_document,
)
from app.tools.resolve_ticket import resolve_ticket

ALLOWED_UPLOAD_EXTENSIONS = {".md", ".txt", ".pdf"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MiniDesk IQ", version="1.0.0", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    requester: str = "employee"


class ChatResponse(BaseModel):
    response: str
    action_taken: str
    sources: list[str]
    tools_called: list[str]
    tool_results: list[dict]
    is_knowledge_gap: bool
    latency_ms: float


class CreateTicketRequest(BaseModel):
    description: str
    category: str
    requester: str


class ApproveRequest(BaseModel):
    approver: str


class ResolveRequest(BaseModel):
    resolver: str = "admin"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = handle_message(request.message, requester=request.requester)
    return result


@app.post("/tickets")
def api_create_ticket(request: CreateTicketRequest):
    ticket = crud.create_ticket(
        description=request.description, category=request.category, requester=request.requester
    )
    return ticket


@app.get("/tickets")
def api_list_tickets(category: Optional[str] = None, status: Optional[str] = None):
    return crud.list_tickets(category=category, status=status)


@app.get("/tickets/{ticket_id}")
def api_get_ticket(ticket_id: int):
    ticket = crud.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/tickets/{ticket_id}/approve")
def api_approve_ticket(ticket_id: int, request: ApproveRequest):
    ticket = crud.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    updated = crud.update_ticket_status(ticket_id, status="in_progress", approver=request.approver)
    crud.log_audit(actor=request.approver, event_type="ticket_approved", detail=f"ticket #{ticket_id}")
    return updated


@app.post("/tickets/{ticket_id}/resolve")
def api_resolve_ticket(ticket_id: int, request: ResolveRequest):
    result = resolve_ticket(ticket_id=ticket_id, resolver=request.resolver)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.get("/logs/queries")
def api_query_logs(limit: int = 500):
    return crud.list_query_logs(limit=limit)


@app.get("/logs/audit")
def api_audit_log(limit: int = 500):
    return crud.list_audit_log(limit=limit)


def _kb_summary() -> dict:
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    count = collection.count()
    docs = set()
    if count > 0:
        data = collection.get(include=["metadatas"])
        docs = {m.get("source") for m in data.get("metadatas", []) if m.get("source")}
    return {"doc_count": len(docs), "chunk_count": count, "docs": sorted(docs)}


@app.get("/knowledge-base/summary")
def knowledge_base_summary():
    return _kb_summary()


@app.post("/knowledge-base/ingest")
def knowledge_base_ingest():
    result = ingest_policies()
    return result


@app.post("/knowledge-base/upload")
async def knowledge_base_upload(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .md, .txt, and .pdf files are supported.")

    content = await file.read()
    text = extract_text_from_upload(file.filename, content)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in the uploaded file.")

    saved_name = save_policy_document(file.filename, text)
    result = ingest_policies(reset=True)
    crud.log_audit(actor="admin", event_type="knowledge_base_upload", detail=f"uploaded {saved_name}")

    return {"uploaded_as": saved_name, **result}


@app.delete("/knowledge-base/documents/{doc_name}")
def knowledge_base_delete_document(doc_name: str):
    existed = delete_document(doc_name)
    if not existed:
        raise HTTPException(status_code=404, detail=f"Document '{doc_name}' not found.")

    crud.log_audit(actor="admin", event_type="knowledge_base_delete", detail=f"deleted {doc_name}")
    return {"deleted": doc_name, **_kb_summary()}
