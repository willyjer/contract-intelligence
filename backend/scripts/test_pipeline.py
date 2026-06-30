"""
CLI test for the ingestion and query pipeline.

Usage:
  # Ingest a file
  python scripts/test_pipeline.py --file sample_contracts/nda_acme_example.pdf

  # Query across all contracts
  python scripts/test_pipeline.py --query "What is the termination notice period in the vendor agreement?"

  # Query scoped to one contract (use the stable doc_id)
  python scripts/test_pipeline.py --query "What is the governing law?" --doc-id fad41552-b511-56ff-a3cc-423b69dfa1db
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.ingestion import ingest_document
from app.services.retrieval import search
from app.services.generation import generate


def run_ingest(file_path: Path) -> None:
    print(f"\n--- Ingesting: {file_path.name} ---")
    result = ingest_document(file_path.read_bytes(), file_path.name, is_demo=True)
    print(f"  doc_id     : {result['doc_id']}")
    print(f"  doc_name   : {result['doc_name']}")
    print(f"  chunk_count: {result['chunk_count']}")
    print("\nPASS: Document ingested successfully.")


def run_query(question: str, doc_id: str | None) -> None:
    print(f"\n--- Query ---")
    print(f"  Q: {question}")
    if doc_id:
        print(f"  Scoped to doc_id: {doc_id}")

    chunks = search(question, doc_id=doc_id)
    print(f"  Retrieved {len(chunks)} chunks", end="")
    if chunks:
        print(f" (top score: {chunks[0].score:.3f})")
    else:
        print()

    if not chunks:
        print("\n  [Path A: no relevant chunks — would return not_found without calling Claude]")
        return

    print(f"\n  Calling Claude...")
    response = generate(question, chunks)

    print(f"\n  found: {response.found}")
    print(f"  answer:\n    {response.answer}")
    if response.citations:
        print(f"\n  citations ({len(response.citations)}):")
        for c in response.citations:
            print(f"    [{c.number}] {c.doc_name}, Page {c.page_number}")
            print(f"         snippet: {c.snippet[:100]}...")
    elif response.found:
        print("\n  (no citations parsed — answer shown without citation chips)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Path to a file to ingest")
    parser.add_argument("--query", help="Question to ask")
    parser.add_argument("--doc-id", help="Scope query to a specific doc_id")
    args = parser.parse_args()

    if not args.file and not args.query:
        parser.error("Provide --file to ingest or --query to ask a question.")

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"ERROR: file not found: {path}")
            sys.exit(1)
        run_ingest(path)

    if args.query:
        run_query(args.query, args.doc_id)


if __name__ == "__main__":
    main()
