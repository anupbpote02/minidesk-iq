# MiniDesk IQ

An agentic IT service desk copilot: RAG over IT/HR policy docs + OpenAI function-calling
tools for ticket creation, status checks, and approvals, with a full audit trail and an
admin analytics dashboard.

## Stack

- FastAPI backend (`app/`)
- OpenAI GPT-4o for chat/tool-calling, `text-embedding-3-small` for embeddings
- ChromaDB (persisted locally) for vector search
- SQLite for tickets, query logs, and audit log
- Streamlit for the employee chat UI and admin dashboard
- Docker + docker-compose for local containerization

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create your `.env` file:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and set `OPENAI_API_KEY` to your own key. Adjust `ADMIN_PASSWORD`
   if you don't want to use the default.

3. Ingest the sample policy docs into ChromaDB:

   ```bash
   python -m app.rag.ingest
   ```

   This chunks and embeds the 5 sample policy docs in `data/policies/` and stores
   them in a local Chroma collection at `./chroma_db`.

4. Initialize the SQLite database (also happens automatically on API startup):

   ```bash
   python -m app.db.database
   ```

## Running locally

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

In a separate terminal, start the employee chat UI:

```bash
streamlit run frontend/chat_app.py
```

And the admin dashboard:

```bash
streamlit run frontend/admin_dashboard.py --server.port 8502
```

The chat UI and dashboard call the API at `API_BASE_URL` (default `http://localhost:8000`).

## Running with Docker

```bash
docker-compose up --build
```

This starts three services:

- `backend` — FastAPI on port 8000
- `frontend` — employee chat UI on port 8501
- `admin` — admin dashboard on port 8502

`./data` and a `chroma_data` volume are mounted so tickets, logs, and the vector
store persist across container restarts. Run the ingest step once against the
running backend container, or exec into it:

```bash
docker exec -it minidesk-iq-backend python -m app.rag.ingest
```

## Evaluating retrieval quality

```bash
python -m eval.run_eval
```

Runs the ~20 question/answer pairs in `eval/eval_questions.json` against the
retriever and prints a hit-rate report (did the expected source doc show up in
the top-k results).

## Project layout

```
minidesk-iq/
├── app/
│   ├── main.py              # FastAPI app entrypoint
│   ├── agent.py             # Core agent logic: RAG vs tool-call orchestration
│   ├── rag/
│   │   ├── ingest.py        # Chunk + embed + store policy docs
│   │   └── retrieve.py      # Similarity search
│   ├── tools/
│   │   ├── schemas.py       # OpenAI function-calling schemas
│   │   ├── create_ticket.py
│   │   ├── check_ticket_status.py
│   │   └── approve_request.py
│   ├── db/
│   │   ├── models.py        # SQLite schema
│   │   ├── database.py      # Connection + init
│   │   └── crud.py          # CRUD helpers for tickets/logs/audit
│   └── config.py
├── data/policies/            # Sample IT/HR policy docs
├── frontend/
│   ├── chat_app.py           # Employee chat UI
│   └── admin_dashboard.py    # Admin analytics dashboard
├── eval/
│   ├── eval_questions.json
│   └── run_eval.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Notes

- The agent logs every interaction to `query_logs` (action taken, source/tool,
  latency, success, knowledge-gap flag) and ticket lifecycle events to `audit_log`.
- If retrieval similarity falls below `RETRIEVAL_SIMILARITY_THRESHOLD` (default
  0.35 in `.env`), the agent responds honestly that it doesn't know instead of
  guessing, and flags the query as a knowledge gap for the admin dashboard.

Pipeline test: test 1
