# Single shared image for all three services (FastAPI backend + 2 Streamlit
# apps). They share the exact same Python dependency set (openai, chromadb,
# fastapi, streamlit, etc.) and codebase, so one image with a per-service
# `command:` override in docker-compose.yml is simpler to build/maintain than
# three near-identical Dockerfiles — the only real cost is each container
# carrying some unused dependencies (e.g. the backend container has streamlit
# installed but never runs it), which is a fine tradeoff at this project size.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY frontend/ ./frontend/
COPY data/ ./data/
COPY eval/ ./eval/
COPY .streamlit/ ./.streamlit/

EXPOSE 8000 8501 8502

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
