"""
Run once to create the two Qdrant collections.
Safe to re-run: skips creation if a collection already exists.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

from app.config import settings

client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

existing = {c.name for c in client.get_collections().collections}

if "contract_chunks" not in existing:
    client.create_collection(
        collection_name="contract_chunks",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    print("Created collection: contract_chunks")
else:
    print("Collection already exists: contract_chunks")

if "contract_documents" not in existing:
    client.create_collection(
        collection_name="contract_documents",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    print("Created collection: contract_documents")
else:
    print("Collection already exists: contract_documents")

# Payload index on doc_id — required for per-document filtering in retrieval
client.create_payload_index(
    collection_name="contract_chunks",
    field_name="doc_id",
    field_schema=PayloadSchemaType.KEYWORD,
)
client.create_payload_index(
    collection_name="contract_chunks",
    field_name="is_demo",
    field_schema=PayloadSchemaType.BOOL,
)
client.create_payload_index(
    collection_name="contract_documents",
    field_name="is_demo",
    field_schema=PayloadSchemaType.BOOL,
)
print("Payload indexes created.")
print("Done.")
