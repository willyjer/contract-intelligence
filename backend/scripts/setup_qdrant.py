"""
Run once to create the two Qdrant collections.

contract_chunks  — dense + sparse vectors (hybrid retrieval)
contract_documents — zero vector (key-value store, never searched)

Re-running this script will WIPE contract_chunks and recreate it with the
current schema. contract_documents is left untouched if it already exists.
Run this whenever the contract_chunks schema changes (e.g. adding sparse vectors).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, SparseVectorParams, SparseIndexParams,
    PayloadSchemaType,
)

from app.config import settings

client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
existing = {c.name for c in client.get_collections().collections}

# contract_chunks: always recreate to ensure schema is current.
# The lifespan function re-seeds demo contracts on next server start.
if "contract_chunks" in existing:
    client.delete_collection("contract_chunks")
    print("Dropped existing contract_chunks collection.")

client.create_collection(
    collection_name="contract_chunks",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    sparse_vectors_config={
        "text-sparse": SparseVectorParams(
            index=SparseIndexParams(on_disk=False)
        )
    },
)
print("Created contract_chunks (dense + sparse).")

if "contract_documents" not in existing:
    client.create_collection(
        collection_name="contract_documents",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    print("Created contract_documents.")
else:
    print("contract_documents already exists — skipped.")

# Payload indexes
client.create_payload_index("contract_chunks", "doc_id", PayloadSchemaType.KEYWORD)
client.create_payload_index("contract_chunks", "is_demo", PayloadSchemaType.BOOL)
client.create_payload_index("contract_documents", "is_demo", PayloadSchemaType.BOOL)
print("Payload indexes created.")
print("Done. Restart the server to re-seed demo contracts.")
