import logging
import uuid
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document as DocxDocument
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from app.config import settings

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=settings.openai_api_key)
qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
CHUNK_COLLECTION = "contract_chunks"
DOCS_COLLECTION = "contract_documents"
MIN_CHUNK_CHARS = 50
EMBED_BATCH_SIZE = 100


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------

def _parse_pdf(file_bytes: bytes) -> list[dict]:
    pages = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append({"page_number": i, "text": text})
    doc.close()
    return pages


def _parse_docx(file_bytes: bytes) -> list[dict]:
    import io
    doc = DocxDocument(io.BytesIO(file_bytes))
    text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return [{"page_number": 1, "text": text}]


def _parse_txt(file_bytes: bytes) -> list[dict]:
    text = file_bytes.decode("utf-8", errors="replace").strip()
    return [{"page_number": 1, "text": text}]


def parse_document(file_bytes: bytes, filename: str) -> list[dict]:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _parse_pdf(file_bytes)
    elif ext == ".docx":
        return _parse_docx(file_bytes)
    elif ext == ".txt":
        return _parse_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ---------------------------------------------------------------------------
# Chunk
# ---------------------------------------------------------------------------

def _is_section_heading(line: str) -> bool:
    """True for lines that should start a new chunk: numbered sections or ALL-CAPS titles."""
    if len(line) > 100:
        return False
    # "1. Purpose", "2. Confidential Information", etc.
    if line and line[0].isdigit() and ". " in line[:5]:
        return True
    # ALL CAPS title lines
    if line.isupper() and len(line) > 3:
        return True
    return False


def chunk_pages(pages: list[dict], doc_id: str, doc_name: str) -> list[dict]:
    chunks = []
    chunk_index = 0
    for page in pages:
        lines = [l.strip() for l in page["text"].split("\n") if l.strip()]
        current_text = ""
        for line in lines:
            if _is_section_heading(line) and len(current_text) >= MIN_CHUNK_CHARS:
                chunks.append({
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "page_number": page["page_number"],
                    "chunk_text": current_text.strip(),
                    "chunk_index": chunk_index,
                })
                chunk_index += 1
                current_text = line + "\n"
            else:
                current_text += line + " "
        if len(current_text.strip()) >= MIN_CHUNK_CHARS:
            chunks.append({
                "doc_id": doc_id,
                "doc_name": doc_name,
                "page_number": page["page_number"],
                "chunk_text": current_text.strip(),
                "chunk_index": chunk_index,
            })
            chunk_index += 1
    return chunks


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------

def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        vectors.extend([item.embedding for item in response.data])
    return vectors


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

def _upsert_chunks(chunks: list[dict], vectors: list[list[float]], is_demo: bool) -> None:
    points = []
    for chunk, vector in zip(chunks, vectors):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={**chunk, "is_demo": is_demo},
            )
        )
    qdrant_client.upsert(collection_name=CHUNK_COLLECTION, points=points)


def _upsert_document(
    doc_id: str,
    doc_name: str,
    doc_type: str,
    pages: list[dict],
    is_demo: bool,
) -> None:
    full_text = "\n\n".join(p["text"] for p in pages)
    page_count = max((p["page_number"] for p in pages), default=1)
    zero_vector = [0.0] * EMBEDDING_DIM

    import datetime

    qdrant_client.upsert(
        collection_name=DOCS_COLLECTION,
        points=[
            PointStruct(
                id=doc_id,
                vector=zero_vector,
                payload={
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "doc_type": doc_type,
                    "full_text": full_text,
                    "page_count": page_count,
                    "extracted_fields": "{}",
                    "uploaded_at": datetime.datetime.utcnow().isoformat(),
                    "is_demo": is_demo,
                },
            )
        ],
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def ingest_document(
    file_bytes: bytes,
    filename: str,
    is_demo: bool = False,
    doc_id: str | None = None,
) -> dict:
    if doc_id is None:
        if is_demo:
            # Stable UUID derived from filename so demo doc_ids survive Qdrant wipes/re-seeds.
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, filename))
        else:
            doc_id = str(uuid.uuid4())

    doc_name = Path(filename).stem.replace("_", " ").title()
    doc_type = Path(filename).suffix.lower().lstrip(".")

    logger.info(f"Ingesting doc_id={doc_id} filename={filename} is_demo={is_demo}")

    pages = parse_document(file_bytes, filename)
    chunks = chunk_pages(pages, doc_id, doc_name)

    if not chunks:
        raise ValueError(f"No usable text found in {filename}")

    logger.info(f"  {len(pages)} pages, {len(chunks)} chunks — embedding...")

    vectors = embed_texts([c["chunk_text"] for c in chunks])

    _upsert_chunks(chunks, vectors, is_demo)
    _upsert_document(doc_id, doc_name, doc_type, pages, is_demo)

    logger.info(f"  Stored {len(chunks)} chunks + 1 document record")
    return {"doc_id": doc_id, "doc_name": doc_name, "chunk_count": len(chunks)}
