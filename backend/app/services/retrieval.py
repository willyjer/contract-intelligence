import logging
from dataclasses import dataclass

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import settings

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=settings.openai_api_key)
qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_COLLECTION = "contract_chunks"
TOP_K = 6
SCORE_THRESHOLD = 0.45


@dataclass
class RetrievedChunk:
    doc_id: str
    doc_name: str
    page_number: int
    chunk_text: str
    chunk_index: int
    score: float


def _embed_query(question: str) -> list[float]:
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=[question])
    return response.data[0].embedding


def search(question: str, doc_id: str | None = None) -> list[RetrievedChunk]:
    query_vector = _embed_query(question)

    search_filter = None
    if doc_id is not None:
        search_filter = Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        )

    results = qdrant_client.search(
        collection_name=CHUNK_COLLECTION,
        query_vector=query_vector,
        limit=TOP_K,
        query_filter=search_filter,
        score_threshold=SCORE_THRESHOLD,
        with_payload=True,
    )

    chunks = [
        RetrievedChunk(
            doc_id=hit.payload["doc_id"],
            doc_name=hit.payload["doc_name"],
            page_number=hit.payload["page_number"],
            chunk_text=hit.payload["chunk_text"],
            chunk_index=hit.payload["chunk_index"],
            score=hit.score,
        )
        for hit in results
    ]

    logger.info(
        "retrieval query=%r doc_id=%s results=%d top_score=%s",
        question[:80],
        doc_id,
        len(chunks),
        f"{chunks[0].score:.3f}" if chunks else "none",
    )
    return chunks
