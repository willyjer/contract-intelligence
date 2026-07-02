import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.limiter import limiter
from app.routers import documents, query

logger = logging.getLogger(__name__)

DEMO_FILENAMES = [
    "nda_acme_example.pdf",
    "vendor_techcorp_widgets.pdf",
    "services_consulting_client.pdf",
    "lease_harbor_startup.pdf",
    "vendor_ambiguous_dynamic_vague.pdf",
]

SAMPLE_DIR = Path(__file__).parent.parent / "sample_contracts"


@asynccontextmanager
async def lifespan(app: FastAPI):
    from qdrant_client import QdrantClient
    from app.services.ingestion import ingest_document
    from app.services.extraction import extract_fields

    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    try:
        existing_ids = {
            str(pt.id)
            for pt in client.scroll(
                "contract_documents", limit=200, with_payload=False, with_vectors=False
            )[0]
        }
    except Exception as exc:
        logger.warning("Could not read contract_documents on startup: %s", exc)
        existing_ids = set()

    for filename in DEMO_FILENAMES:
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, filename))
        if doc_id not in existing_ids:
            path = SAMPLE_DIR / filename
            if path.exists():
                logger.info("Seeding missing demo contract: %s", filename)
                result = ingest_document(path.read_bytes(), filename, is_demo=True)
                extract_fields(result["doc_id"])
            else:
                logger.warning("Demo contract file not found: %s", path)

    yield


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded", "detail": str(exc.detail)},
    )


app = FastAPI(title="Contract Intelligence Assistant", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(query.router)


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
