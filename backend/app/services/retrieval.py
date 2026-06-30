import logging
from dataclasses import dataclass

import cohere
from fastembed import SparseTextEmbedding
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue,
    Prefetch, FusionQuery, Fusion, SparseVector,
)

from app.config import settings

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=settings.openai_api_key)
qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
cohere_client = cohere.ClientV2(api_key=settings.cohere_api_key)

_sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_COLLECTION = "contract_chunks"
RETRIEVE_K = 20   # candidates from hybrid search before reranking
TOP_K = 6         # final results passed to generation after reranking


@dataclass
class RetrievedChunk:
    doc_id: str
    doc_name: str
    page_number: int
    chunk_text: str
    chunk_index: int
    score: float


def _embed_query_dense(question: str) -> list[float]:
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=[question])
    return response.data[0].embedding


def _embed_query_sparse(question: str) -> SparseVector:
    embedding = list(_sparse_model.embed([question]))[0]
    return SparseVector(indices=embedding.indices.tolist(), values=embedding.values.tolist())


def search(question: str, doc_id: str | None = None) -> list[RetrievedChunk]:
    search_filter = None
    if doc_id is not None:
        search_filter = Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        )

    dense_vec = _embed_query_dense(question)
    sparse_vec = _embed_query_sparse(question)

    # Hybrid search: dense + sparse via Qdrant native RRF fusion
    result = qdrant_client.query_points(
        collection_name=CHUNK_COLLECTION,
        prefetch=[
            Prefetch(query=dense_vec, using=None, limit=RETRIEVE_K),
            Prefetch(query=sparse_vec, using="text-sparse", limit=RETRIEVE_K),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=RETRIEVE_K,
        query_filter=search_filter,
        with_payload=True,
    )
    candidates = result.points

    if not candidates:
        logger.info("retrieval query=%r — no candidates", question[:80])
        return []

    # Cohere rerank
    candidate_texts = [hit.payload["chunk_text"] for hit in candidates]
    rerank_response = cohere_client.rerank(
        model="rerank-v3.5",
        query=question,
        documents=candidate_texts,
        top_n=TOP_K,
    )

    chunks = []
    for result in rerank_response.results:
        payload = candidates[result.index].payload
        chunks.append(
            RetrievedChunk(
                doc_id=payload["doc_id"],
                doc_name=payload["doc_name"],
                page_number=payload["page_number"],
                chunk_text=payload["chunk_text"],
                chunk_index=payload["chunk_index"],
                score=result.relevance_score,
            )
        )

    logger.info(
        "retrieval query=%r doc_id=%s candidates=%d reranked=%d top_score=%s",
        question[:80],
        doc_id,
        len(candidates),
        len(chunks),
        f"{chunks[0].score:.3f}" if chunks else "none",
    )
    return chunks
