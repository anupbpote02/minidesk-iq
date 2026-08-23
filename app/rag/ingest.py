"""Loads policy markdown docs, chunks them, embeds with OpenAI, and stores in ChromaDB."""

import glob
import io
import os
import re

import chromadb
from openai import OpenAI

from app.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    POLICIES_DIR,
)


def get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def get_or_create_collection(client: chromadb.PersistentClient):
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Splits text into overlapping character-based chunks, breaking on paragraph
    boundaries where possible so chunks stay reasonably coherent."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > chunk_size:
                # Paragraph itself is too long; hard-split with overlap.
                start = 0
                while start < len(para):
                    end = start + chunk_size
                    chunks.append(para[start:end])
                    start = end - overlap
            else:
                current = para
                continue
            current = ""
    if current:
        chunks.append(current)

    # Add character-level overlap between adjacent chunks for better retrieval context.
    overlapped = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            overlapped.append(chunk)
        else:
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(f"{prev_tail}\n{chunk}")
    return overlapped


def load_policy_documents(policies_dir: str = POLICIES_DIR) -> dict[str, str]:
    docs = {}
    for path in sorted(glob.glob(os.path.join(policies_dir, "*.md"))):
        name = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as f:
            docs[name] = f.read()
    return docs


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def ingest_policies(policies_dir: str = POLICIES_DIR, reset: bool = True) -> dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Create a .env file from .env.example.")

    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    chroma_client = get_chroma_client()

    if reset:
        try:
            chroma_client.delete_collection(CHROMA_COLLECTION_NAME)
        except Exception:
            pass

    collection = get_or_create_collection(chroma_client)

    docs = load_policy_documents(policies_dir)
    if not docs:
        raise RuntimeError(f"No policy documents found in {policies_dir}")

    all_chunks: list[str] = []
    all_ids: list[str] = []
    all_metadatas: list[dict] = []

    for doc_name, text in docs.items():
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{doc_name}::chunk_{i}")
            all_metadatas.append({"source": doc_name, "chunk_index": i})

    # Batch embeddings to stay well within request size limits.
    batch_size = 64
    embeddings: list[list[float]] = []
    for start in range(0, len(all_chunks), batch_size):
        batch = all_chunks[start : start + batch_size]
        embeddings.extend(embed_texts(openai_client, batch))

    collection.add(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )

    return {
        "doc_count": len(docs),
        "chunk_count": len(all_chunks),
        "docs": list(docs.keys()),
    }


def extract_text_from_upload(filename: str, content: bytes) -> str:
    """Extracts plain text from an uploaded .md/.txt or .pdf file's raw bytes."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages).strip()
    return content.decode("utf-8", errors="ignore").strip()


def save_policy_document(filename: str, text: str, policies_dir: str = POLICIES_DIR) -> str:
    """Saves extracted text as a new .md file in the policies directory, uniquifying
    the name if it collides with an existing document. Returns the saved filename."""
    base = os.path.splitext(os.path.basename(filename))[0]
    safe_base = re.sub(r"[^A-Za-z0-9_-]+", "_", base).strip("_") or "uploaded_doc"

    candidate = f"{safe_base}.md"
    counter = 1
    while os.path.exists(os.path.join(policies_dir, candidate)):
        candidate = f"{safe_base}_{counter}.md"
        counter += 1

    os.makedirs(policies_dir, exist_ok=True)
    with open(os.path.join(policies_dir, candidate), "w", encoding="utf-8") as f:
        f.write(text)
    return candidate


def delete_document(doc_name: str, policies_dir: str = POLICIES_DIR) -> bool:
    """Deletes a document's chunks from ChromaDB and removes its file from the
    policies directory. Returns True if the document existed and was removed."""
    file_path = os.path.join(policies_dir, doc_name)
    existed = os.path.exists(file_path)

    client = get_chroma_client()
    collection = get_or_create_collection(client)
    collection.delete(where={"source": doc_name})

    if existed:
        os.remove(file_path)

    return existed


if __name__ == "__main__":
    result = ingest_policies()
    print(f"Ingested {result['doc_count']} documents into {result['chunk_count']} chunks:")
    for doc in result["docs"]:
        print(f"  - {doc}")
