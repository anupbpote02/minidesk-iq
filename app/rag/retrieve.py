"""Retrieval logic: embeds a query and runs similarity search against ChromaDB."""

from dataclasses import dataclass

from openai import OpenAI

from app.config import (
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    RETRIEVAL_SIMILARITY_THRESHOLD,
    RETRIEVAL_TOP_K,
)
from app.rag.ingest import get_chroma_client, get_or_create_collection

_openai_client = OpenAI(api_key=OPENAI_API_KEY)


@dataclass
class RetrievedChunk:
    text: str
    source: str
    chunk_index: int
    similarity: float


def _embed_query(query: str) -> list[float]:
    response = _openai_client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
    return response.data[0].embedding


def retrieve(query: str, top_k: int = RETRIEVAL_TOP_K) -> list[RetrievedChunk]:
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    if collection.count() == 0:
        return []

    query_embedding = _embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )

    chunks: list[RetrievedChunk] = []
    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, distance in zip(docs, metadatas, distances):
        # Chroma cosine "distance" -> similarity = 1 - distance
        similarity = 1 - distance
        chunks.append(
            RetrievedChunk(
                text=doc,
                source=meta.get("source", "unknown"),
                chunk_index=meta.get("chunk_index", -1),
                similarity=similarity,
            )
        )
    return chunks


def best_match_above_threshold(
    chunks: list[RetrievedChunk], threshold: float = RETRIEVAL_SIMILARITY_THRESHOLD
) -> bool:
    return bool(chunks) and chunks[0].similarity >= threshold


def format_context(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for chunk in chunks:
        parts.append(f"[Source: {chunk.source}]\n{chunk.text}")
    return "\n\n---\n\n".join(parts)
