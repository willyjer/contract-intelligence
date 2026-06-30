import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.config import settings
from app.limiter import limiter
from app.services.generation import generate
from app.services.retrieval import search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    question: str
    doc_id: str | None = None


class CitationRefResponse(BaseModel):
    number: int
    doc_name: str
    page_number: int
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    found: bool
    citations: list[CitationRefResponse]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("", response_model=QueryResponse)
@limiter.limit(f"{settings.query_rate_limit_per_hour}/hour")
async def query_documents(request: Request, body: QueryRequest):
    chunks = search(body.question, doc_id=body.doc_id)
    response = generate(body.question, chunks)

    return QueryResponse(
        answer=response.answer,
        found=response.found,
        citations=[
            CitationRefResponse(
                number=c.number,
                doc_name=c.doc_name,
                page_number=c.page_number,
                snippet=c.snippet,
            )
            for c in response.citations
        ],
    )
