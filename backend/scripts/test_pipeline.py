"""
CLI test for the ingestion pipeline.

Usage:
  python scripts/test_pipeline.py --file sample_contracts/nda_acme_example.pdf
  python scripts/test_pipeline.py --file sample_contracts/nda_acme_example.pdf --query "What is the termination period?"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.ingestion import ingest_document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to a PDF/DOCX/TXT file to ingest")
    parser.add_argument("--query", help="Optional: question to test retrieval (Session 2+)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        sys.exit(1)

    print(f"\n--- Ingesting: {path.name} ---")
    file_bytes = path.read_bytes()

    result = ingest_document(file_bytes, path.name, is_demo=True)

    print(f"  doc_id     : {result['doc_id']}")
    print(f"  doc_name   : {result['doc_name']}")
    print(f"  chunk_count: {result['chunk_count']}")
    print("\nPASS: Document ingested successfully.")

    if args.query:
        print(f"\n--- Retrieval test (Session 2+) ---")
        print("Retrieval not yet implemented. Build Session 2 next.")


if __name__ == "__main__":
    main()
