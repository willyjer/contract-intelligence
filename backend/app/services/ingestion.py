import base64
import logging
import uuid
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document as DocxDocument
from fastembed import SparseTextEmbedding
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, SparseVector

from app.config import settings

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=settings.openai_api_key)
qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

# Loaded once at module import; downloads ~few MB on first use.
_sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
CHUNK_COLLECTION = "contract_chunks"
DOCS_COLLECTION = "contract_documents"
MIN_CHUNK_CHARS = 50
EMBED_BATCH_SIZE = 100
OCR_MIN_CHARS = 20  # pages with fewer chars than this get OCR treatment


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------

def _ocr_page_with_claude(page: fitz.Page) -> str:
    """Render a scanned page as PNG and extract text via Claude vision."""
    import anthropic
    pix = page.get_pixmap(dpi=200)
    img_b64 = base64.standard_b64encode(pix.tobytes("png")).decode()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": img_b64},
                },
                {
                    "type": "text",
                    "text": "Extract all text from this document page. Return only the text content, preserving paragraph breaks. Do not add commentary.",
                },
            ],
        }],
    )
    return msg.content[0].text.strip()


def _parse_pdf(file_bytes: bytes) -> list[dict]:
    pages = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if len(text) < OCR_MIN_CHARS:
            logger.info("Page %d has %d chars — attempting OCR via Claude vision", i, len(text))
            try:
                text = _ocr_page_with_claude(page)
            except Exception as e:
                logger.warning("OCR failed for page %d: %s", i, e)
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
    if len(line) > 100:
        return False
    if line and line[0].isdigit() and ". " in line[:5]:
        return True
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
        batch = texts[i: i + EMBED_BATCH_SIZE]
        response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        vectors.extend([item.embedding for item in response.data])
    return vectors


def sparse_embed_texts(texts: list[str]) -> list[SparseVector]:
    embeddings = list(_sparse_model.embed(texts))
    return [
        SparseVector(indices=e.indices.tolist(), values=e.values.tolist())
        for e in embeddings
    ]


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

def _upsert_chunks(
    chunks: list[dict],
    dense_vectors: list[list[float]],
    sparse_vectors: list[SparseVector],
    is_demo: bool,
) -> None:
    points = []
    for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={"": dense, "text-sparse": sparse},
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
    import datetime
    full_text = "\n\n".join(p["text"] for p in pages)
    page_count = max((p["page_number"] for p in pages), default=1)
    zero_vector = [0.0] * EMBEDDING_DIM

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
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, filename))
        else:
            doc_id = str(uuid.uuid4())

    doc_name = Path(filename).stem.replace("_", " ").title()
    doc_type = Path(filename).suffix.lower().lstrip(".")

    logger.info("Ingesting doc_id=%s filename=%s is_demo=%s", doc_id, filename, is_demo)

    pages = parse_document(file_bytes, filename)
    chunks = chunk_pages(pages, doc_id, doc_name)

    if not chunks:
        raise ValueError(f"No usable text found in {filename}")

    logger.info("  %d pages, %d chunks — embedding...", len(pages), len(chunks))

    texts = [c["chunk_text"] for c in chunks]
    dense_vectors = embed_texts(texts)
    sparse_vectors = sparse_embed_texts(texts)

    _upsert_chunks(chunks, dense_vectors, sparse_vectors, is_demo)
    _upsert_document(doc_id, doc_name, doc_type, pages, is_demo)

    logger.info("  Stored %d chunks + 1 document record", len(chunks))
    return {"doc_id": doc_id, "doc_name": doc_name, "chunk_count": len(chunks)}
