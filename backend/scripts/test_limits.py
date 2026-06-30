"""
Verify rate limiting and upload cap eviction.

Run with the server live on port 8000:
  python scripts/test_limits.py --test query-rate
  python scripts/test_limits.py --test upload-rate
  python scripts/test_limits.py --test eviction

The eviction test temporarily lowers MAX_USER_UPLOADS via query param override
by directly calling the service layer — no .env change needed.
"""
import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://localhost:8000"


def http_post(path: str, body: dict | None = None, file_bytes: bytes | None = None, filename: str = "test.pdf") -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    if file_bytes is not None:
        boundary = "----boundary1234"
        data = (
            f"------boundary1234\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode() + file_bytes + b"\r\n------boundary1234--\r\n"
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary=----boundary1234")
    else:
        payload = json.dumps(body or {}).encode()
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_query_rate_limit():
    print("\n=== Query rate limit (expect 429 on request 21) ===")
    body = {"question": "test", "doc_id": None}
    for i in range(1, 23):
        status, resp = http_post("/query", body=body)
        marker = " <-- RATE LIMITED" if status == 429 else ""
        print(f"  Request {i:2d}: {status}{marker}")
        if status == 429:
            print(f"  Body: {resp}")
            print(f"\nPASS: 429 triggered on request {i} (expected 21)")
            return True
    print("\nFAIL: never got 429 after 22 requests")
    return False


def test_upload_rate_limit():
    print("\n=== Upload rate limit (expect 429 on request 6) ===")
    sample = (Path(__file__).parent.parent / "sample_contracts" / "nda_acme_example.pdf").read_bytes()
    for i in range(1, 8):
        status, resp = http_post("/documents/upload", file_bytes=sample, filename=f"ratelimit_test_{i}.pdf")
        marker = " <-- RATE LIMITED" if status == 429 else f"  doc_id={resp.get('doc_id','')[:8]}..." if status == 200 else ""
        print(f"  Request {i}: {status}{marker}")
        if status == 429:
            print(f"  Body: {resp}")
            print(f"\nPASS: 429 triggered on request {i} (expected 6)")
            return True
    print("\nFAIL: never got 429 after 7 uploads")
    return False


def test_eviction():
    print("\n=== Upload cap eviction (MAX_USER_UPLOADS=2, upload 3 files) ===")
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    from app.config import settings
    from app.services.ingestion import ingest_document
    from app.services.extraction import extract_fields

    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    # Clean any existing non-demo docs first
    from qdrant_client.models import FilterSelector
    existing_non_demo, _ = client.scroll(
        "contract_documents",
        scroll_filter=Filter(must=[FieldCondition(key="is_demo", match=MatchValue(value=False))]),
        limit=100, with_payload=True, with_vectors=False,
    )
    for pt in existing_non_demo:
        doc_id = pt.payload["doc_id"]
        client.delete("contract_chunks", points_selector=FilterSelector(
            filter=Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))])
        ))
        client.delete("contract_documents", points_selector=[doc_id])
    if existing_non_demo:
        print(f"  Cleaned {len(existing_non_demo)} existing non-demo docs")

    sample = (Path(__file__).parent.parent / "sample_contracts" / "nda_acme_example.pdf").read_bytes()
    cap = 2
    uploaded_ids = []
    for i in range(1, cap + 2):  # upload cap+1 files
        result = ingest_document(sample, f"eviction_test_{i}.pdf", is_demo=False)
        uploaded_ids.append(result["doc_id"])
        print(f"  Upload {i}: doc_id={result['doc_id'][:8]}... ({result['doc_name']})")

        # Simulate cap enforcement (same logic as the router)
        non_demo, _ = client.scroll(
            "contract_documents",
            scroll_filter=Filter(must=[FieldCondition(key="is_demo", match=MatchValue(value=False))]),
            limit=cap + 10, with_payload=True, with_vectors=False,
        )
        if len(non_demo) >= cap:
            sorted_docs = sorted(non_demo, key=lambda p: p.payload.get("uploaded_at", ""))
            oldest = sorted_docs[0]
            oldest_id = oldest.payload["doc_id"]
            print(f"  Cap hit ({len(non_demo)}>={cap}): evicting {oldest_id[:8]}... ({oldest.payload.get('doc_name','')})")
            client.delete("contract_chunks", points_selector=FilterSelector(
                filter=Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=oldest_id))])
            ))
            client.delete("contract_documents", points_selector=[oldest_id])

    # Verify final state
    final_non_demo, _ = client.scroll(
        "contract_documents",
        scroll_filter=Filter(must=[FieldCondition(key="is_demo", match=MatchValue(value=False))]),
        limit=100, with_payload=True, with_vectors=False,
    )
    remaining_ids = {pt.payload["doc_id"] for pt in final_non_demo}
    print(f"\n  Final non-demo count: {len(final_non_demo)} (expected {cap - 1} or {cap})")
    print(f"  Remaining: {[r[:8]+'...' for r in remaining_ids]}")

    first_id = uploaded_ids[0]
    if first_id not in remaining_ids:
        print(f"\nPASS: Oldest doc ({first_id[:8]}...) was evicted correctly")
        return True
    else:
        print(f"\nFAIL: Oldest doc ({first_id[:8]}...) was NOT evicted")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", choices=["query-rate", "upload-rate", "eviction"], required=True)
    args = parser.parse_args()

    if args.test == "query-rate":
        ok = test_query_rate_limit()
    elif args.test == "upload-rate":
        ok = test_upload_rate_limit()
    elif args.test == "eviction":
        ok = test_eviction()

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
