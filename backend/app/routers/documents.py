import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointIdsList,
)

from app.config import settings
from app.limiter import limiter
from app.services.extraction import extract_fields
from app.services.ingestion import ingest_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
DOCS_COLLECTION = "contract_documents"
CHUNKS_COLLECTION = "contract_chunks"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class DocumentSummary(BaseModel):
    doc_id: str
    doc_name: str
    doc_type: str
    page_count: int
    uploaded_at: str


class DocumentDetail(BaseModel):
    doc_id: str
    doc_name: str
    full_text: str
    extracted_fields: dict
    page_count: int


class UploadResult(BaseModel):
    doc_id: str
    doc_name: str
    chunk_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _evict_oldest_non_demo() -> None:
    results, _ = qdrant_client.scroll(
        DOCS_COLLECTION,
        scroll_filter=Filter(
            must=[FieldCondition(key="is_demo", match=MatchValue(value=False))]
        ),
        limit=settings.max_user_uploads + 10,
        with_payload=True,
        with_vectors=False,
    )

    if len(results) < settings.max_user_uploads:
        return

    sorted_docs = sorted(results, key=lambda p: p.payload.get("uploaded_at", ""))
    oldest = sorted_docs[0]
    doc_id = oldest.payload["doc_id"]
    doc_name = oldest.payload.get("doc_name", doc_id)

    logger.info("Evicting oldest non-demo doc: %s (%s)", doc_id, doc_name)

    qdrant_client.delete(
        CHUNKS_COLLECTION,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            )
        ),
    )
    qdrant_client.delete(
        DOCS_COLLECTION,
        points_selector=PointIdsList(points=[doc_id]),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[DocumentSummary])
def list_documents():
    results, _ = qdrant_client.scroll(
        DOCS_COLLECTION,
        limit=200,
        with_payload=True,
        with_vectors=False,
    )
    docs = []
    for pt in results:
        p = pt.payload
        docs.append(
            DocumentSummary(
                doc_id=p["doc_id"],
                doc_name=p["doc_name"],
                doc_type=p.get("doc_type", ""),
                page_count=p.get("page_count", 1),
                uploaded_at=p.get("uploaded_at", ""),
            )
        )
    docs.sort(key=lambda d: (not _is_demo(d.doc_id, results), d.doc_name))
    return docs


def _is_demo(doc_id: str, results) -> bool:
    for pt in results:
        if pt.payload["doc_id"] == doc_id:
            return pt.payload.get("is_demo", False)
    return False


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: str):
    import json

    results = qdrant_client.retrieve(
        DOCS_COLLECTION,
        ids=[doc_id],
        with_payload=True,
        with_vectors=False,
    )
    if not results:
        raise HTTPException(status_code=404, detail="Document not found")

    p = results[0].payload
    raw_fields = p.get("extracted_fields", "{}")
    try:
        fields = json.loads(raw_fields)
    except Exception:
        fields = {}

    return DocumentDetail(
        doc_id=p["doc_id"],
        doc_name=p["doc_name"],
        full_text=p.get("full_text", ""),
        extracted_fields=fields,
        page_count=p.get("page_count", 1),
    )


@router.post("/upload", response_model=UploadResult)
@limiter.limit(f"{settings.upload_rate_limit_per_hour}/hour")
async def upload_document(request: Request, file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit")

    _evict_oldest_non_demo()

    result = ingest_document(file_bytes, file.filename, is_demo=False)
    extract_fields(result["doc_id"])

    return UploadResult(
        doc_id=result["doc_id"],
        doc_name=result["doc_name"],
        chunk_count=result["chunk_count"],
    )
